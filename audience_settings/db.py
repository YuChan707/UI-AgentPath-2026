"""Read the product's features+settings; persist audience_responses (asyncpg)."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass

import asyncpg

_SCORE_COLS = (
    "confident_score",
    "complexity_score",
    "security_score",
    "engagement_score",
    "interest_score",
    "value_perceived_score",
    "general_sentiment_score",
)


def _dsn() -> str:
    url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/onlooker")
    if "+asyncpg" in url:
        url = url.replace("+asyncpg", "")
    if url.startswith("postgresql+"):
        url = "postgresql://" + url.split("://", 1)[1]
    return url


@dataclass
class ProductInput:
    features: list[dict]
    settings: dict


async def fetch_input(id_product: str) -> ProductInput | None:
    conn = await asyncpg.connect(dsn=_dsn())
    try:
        row = await conn.fetchrow(
            "SELECT features, settings FROM products WHERE id_product = $1", id_product
        )
    finally:
        await conn.close()
    if not row:
        return None
    features = row["features"] or []
    if isinstance(features, str):
        features = json.loads(features)
    settings = row["settings"] or {}
    if isinstance(settings, str):
        settings = json.loads(settings)
    return ProductInput(features=features, settings=settings)


async def save_responses(id_product: str, rows: list[dict]) -> None:
    """Insert one audience_responses row per (group, feature); mark product reacting."""
    cols = "id_product, id_audience, id_feature, " + ", ".join(_SCORE_COLS)
    placeholders = ", ".join(f"${i}" for i in range(1, 4 + len(_SCORE_COLS)))
    sql = f"INSERT INTO audience_responses ({cols}) VALUES ({placeholders})"
    conn = await asyncpg.connect(dsn=_dsn())
    try:
        async with conn.transaction():
            for r in rows:
                await conn.execute(
                    sql,
                    id_product,
                    r["id_audience"],
                    r["id_feature"],
                    *[r["scores"].get(c, 0.5) for c in _SCORE_COLS],
                )
            await conn.execute(
                "UPDATE products SET status = 'reacting' WHERE id_product = $1", id_product
            )
    finally:
        await conn.close()


__all__ = ["ProductInput", "fetch_input", "save_responses"]
