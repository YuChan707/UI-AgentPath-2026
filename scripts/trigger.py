#!/usr/bin/env python3
"""End-to-end pipeline trigger (no UI needed).

Inserts a product document into Postgres and kicks the embeding-service over HTTP
(`POST /events/document-uploaded`) — the same CloudEvent shape Dapr delivers — so
the whole chain runs: embeding -> features -> audience -> develop-analysis.
Then it polls `products.status` until `analyzed` (or timeout) and prints results.

Prereqs: the stack is up
    docker compose up -d
    docker compose --profile pipeline up --build
    ollama pull llama3.1 && ollama pull nomic-embed-text

Usage:
    python scripts/trigger.py                 # built-in sample .txt
    python scripts/trigger.py path/to/file.pdf
    DATABASE_URL=... EMBEDING_URL=http://localhost:8100 python scripts/trigger.py
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path

import asyncpg
import httpx

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/onlooker")
EMBEDING_URL = os.getenv("EMBEDING_URL", "http://localhost:8100").rstrip("/")
ACCEPTED = {"txt", "md", "pdf", "pptx", "docx"}

SAMPLE = (
    "OnLooker Pro is a team analytics dashboard.\n\n"
    "Feature: Real-time KPI tiles that update as data streams in.\n"
    "Feature: Role-based access so managers and analysts see different views.\n"
    "Feature: One-click PDF export of any report.\n"
    "Feature: Anomaly alerts when a metric crosses a threshold.\n"
)


def _dsn() -> str:
    url = DATABASE_URL
    if "+asyncpg" in url:
        url = url.replace("+asyncpg", "")
    if url.startswith("postgresql+"):
        url = "postgresql://" + url.split("://", 1)[1]
    return url


async def insert_product(conn, name: str, doc_type: str, content: bytes) -> str:
    settings = {
        "audience_type": "", "audience_enviroment": "", "audience_area": "",
        "audience_size": 1500, "gender_dstn": "generic", "age_dstn": "20-45",
        "main_goal": "", "response_goal": "",
    }
    insights = {
        "detect_strengts": True, "detect_weakness": True,
        "detect_potential": True, "general_report": True,
    }
    row = await conn.fetchrow(
        """INSERT INTO products (document_name, doc_type, content, settings, insights, status)
           VALUES ($1, $2, $3, $4::jsonb, $5::jsonb, 'uploaded') RETURNING id_product""",
        name, doc_type, content, json.dumps(settings), json.dumps(insights),
    )
    return str(row["id_product"])


async def kick(id_product: str, doc_type: str) -> None:
    async with httpx.AsyncClient(timeout=30) as c:
        r = await c.post(
            f"{EMBEDING_URL}/events/document-uploaded",
            json={"data": {"id_product": id_product, "doc_type": doc_type}},
        )
        r.raise_for_status()


async def watch(conn, id_product: str, timeout: float = 300.0) -> None:
    last = None
    waited = 0.0
    while waited < timeout:
        row = await conn.fetchrow("SELECT status FROM products WHERE id_product=$1", id_product)
        n_resp = await conn.fetchval("SELECT count(*) FROM audience_responses WHERE id_product=$1", id_product)
        status = row["status"] if row else "?"
        if (status, n_resp) != last:
            print(f"  [{waited:5.0f}s] status={status} audience_responses={n_resp}")
            last = (status, n_resp)
        if status == "analyzed":
            an = await conn.fetchrow(
                "SELECT strengths, weakness, points_with_potential, aggregate_scores "
                "FROM product_analysis WHERE id_product=$1", id_product)
            print("\n✓ DONE. product_analysis:")
            print(json.dumps({k: (json.loads(v) if isinstance(v, str) else v) for k, v in dict(an).items()}, indent=2, ensure_ascii=False))
            return
        await asyncio.sleep(3)
        waited += 3
    print(f"\n⏱ timeout after {timeout:.0f}s (status={last}). Check service logs.")


async def main() -> int:
    arg = sys.argv[1] if len(sys.argv) > 1 else None
    if arg:
        p = Path(arg)
        name, content = p.name, p.read_bytes()
        doc_type = p.suffix.lstrip(".").lower()
    else:
        name, content, doc_type = "sample.txt", SAMPLE.encode(), "txt"
    if doc_type not in ACCEPTED:
        print(f"unsupported type .{doc_type}; accepted: {sorted(ACCEPTED)}")
        return 2

    try:
        conn = await asyncpg.connect(dsn=_dsn())
    except Exception as exc:
        print(f"✗ cannot reach Postgres at {_dsn()} — is the stack up? ({type(exc).__name__}: {exc})")
        return 1
    try:
        pid = await insert_product(conn, name, doc_type, content)
        print(f"inserted product {pid} ({name}, .{doc_type})")
        try:
            await kick(pid, doc_type)
            print(f"kicked embeding-service at {EMBEDING_URL}; watching...\n")
        except Exception as exc:
            print(f"✗ cannot reach embeding-service at {EMBEDING_URL} ({type(exc).__name__}: {exc})")
            print("  Product is inserted; start the pipeline profile and re-kick.")
            return 1
        await watch(conn, pid)
    finally:
        await conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
