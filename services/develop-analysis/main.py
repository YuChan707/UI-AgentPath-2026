"""
develop-analysis
  Subscribes: audience-processed
  Publishes:  report-ready, pipeline-status

Pipeline step 4 of 4:
  read audience metrics + insight_flags
  → for each enabled flag, generate a report section via Ollama
  → persist final_report to pipeline_runs
  → publish report-ready
"""
import json
import logging
import os
import asyncio
import uuid
from contextlib import asynccontextmanager
from typing import Any

import asyncpg
import httpx
import ollama
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("develop-analysis")

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/onlooker")
OLLAMA_HOST  = os.getenv("OLLAMA_HOST", "http://localhost:11434")
LLM_MODEL    = os.getenv("LLM_MODEL", "llama3.2")
DAPR_HTTP    = f"http://localhost:{os.getenv('DAPR_HTTP_PORT', '3503')}"
PUBSUB_NAME  = "onlooker-pubsub"

_pool: asyncpg.Pool | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _pool
    dsn  = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
    _pool = await asyncpg.create_pool(dsn, min_size=2, max_size=5)
    log.info("develop-analysis ready")
    yield
    await _pool.close()


app = FastAPI(title="develop-analysis", lifespan=lifespan)


@app.get("/dapr/subscribe")
def dapr_subscribe():
    return [{"pubsubname": PUBSUB_NAME, "topic": "audience-processed", "route": "/audience-processed"}]


async def _publish(topic: str, data: dict[str, Any]) -> None:
    async with httpx.AsyncClient() as c:
        await c.post(f"{DAPR_HTTP}/v1.0/publish/{PUBSUB_NAME}/{topic}", json=data, timeout=30)


async def _status(run_id: str, stage: str, detail: str = "") -> None:
    await _publish("pipeline-status", {"run_id": run_id, "stage": stage, "detail": detail})


def _build_prompt(section: str, reactions: list[dict], metrics: dict) -> str:
    top = sorted(reactions, key=lambda r: r.get("importance", 5), reverse=True)[:5]
    feature_lines = "\n".join(
        f"- {r.get('feature','')} "
        f"(engagement={r.get('engagement','?')}, approval={r.get('approval','?')}): "
        f"{r.get('reaction_thought','')}"
        for r in top
    )
    m_str = (
        f"engagement_avg={metrics.get('engagement_avg')} "
        f"approval_avg={metrics.get('approval_avg')} "
        f"clarity_avg={metrics.get('clarity_avg')} "
        f"relevance_avg={metrics.get('relevance_avg')}"
    )

    prompts: dict[str, str] = {
        "detect_strengths": (
            f"Audience metrics: {m_str}\n"
            f"Top features and reactions:\n{feature_lines}\n\n"
            "List 3-5 KEY STRENGTHS of this content for the given audience.\n"
            'Return ONLY JSON: {"strengths": ["strength 1", "strength 2", ...]}'
        ),
        "detect_weaknesses": (
            f"Audience metrics: {m_str}\n"
            f"Features:\n{feature_lines}\n\n"
            "List 3-5 WEAKNESSES or improvement areas this content has for the audience.\n"
            'Return ONLY JSON: {"weaknesses": ["weakness 1", ...]}'
        ),
        "detect_potential": (
            f"Audience: {metrics.get('audience_type', '')}\nMetrics: {m_str}\n"
            f"Features:\n{feature_lines}\n\n"
            "Suggest 3-5 OPPORTUNITIES to improve this content's impact on the audience.\n"
            'Return ONLY JSON: {"opportunities": ["opportunity 1", ...]}'
        ),
        "general_report": (
            f"Audience: {metrics.get('audience_type', '')} (size ~{metrics.get('audience_size', 100)})\n"
            f"Metrics: {m_str}\n"
            "Write a concise executive summary of this content's effectiveness. "
            "Include overall assessment and top 2 actionable recommendations.\n"
            'Return ONLY JSON: {"summary": "<executive summary string>"}'
        ),
    }
    return prompts.get(section, "")


def _gen_section_sync(section: str, reactions: list[dict], metrics: dict) -> dict:
    prompt = _build_prompt(section, reactions, metrics)
    if not prompt:
        return {}
    client = ollama.Client(host=OLLAMA_HOST)
    try:
        resp = client.chat(
            model=LLM_MODEL,
            messages=[{"role": "user", "content": prompt}],
            format="json",
            options={"temperature": 0.3},
        )
        return json.loads(resp["message"]["content"])
    except Exception as exc:
        log.warning("section '%s' generation failed: %s", section, exc)
        return {}


@app.post("/audience-processed")
async def on_audience_processed(request: Request) -> JSONResponse:
    body          = await request.json()
    data          = body.get("data", body)
    run_id        = data["run_id"]
    metrics       = data.get("metrics", {})
    reactions     = data.get("reactions", [])
    insight_flags = data.get("insight_flags", {})

    log.info("run=%s", run_id)
    await _status(run_id, "analysis:started", "Generating insight sections")

    # Default all flags to True if not specified
    sections = [
        s for s in ("detect_strengths", "detect_weaknesses", "detect_potential", "general_report")
        if insight_flags.get(s, True)
    ]

    # Generate all sections in parallel (independent of each other)
    loop = asyncio.get_event_loop()
    results = await asyncio.gather(*[
        loop.run_in_executor(None, _gen_section_sync, s, reactions, metrics)
        for s in sections
    ])

    report = {
        "run_id":   run_id,
        "metrics":  metrics,
        "sections": {s: r for s, r in zip(sections, results)},
    }

    # Persist
    async with _pool.acquire() as conn:
        await conn.execute(
            """
            UPDATE pipeline_runs
               SET final_report = $1, status = 'report_ready'
             WHERE run_id = $2
            """,
            json.dumps(report),
            uuid.UUID(run_id),
        )

    await _status(run_id, "analysis:complete", "Final report ready")
    await _publish("report-ready", {"run_id": run_id, "report": report})

    return JSONResponse({"status": "SUCCESS"})
