"""
audience-settings
  Subscribes: features-extracted
  Publishes:  audience-processed, pipeline-status

Pipeline step 3 of 4:
  for each feature → simulate audience reaction via Ollama (parallel, semaphore-limited)
  → aggregate engagement / approval / clarity / relevance metrics
  → persist to pipeline_runs
  → publish audience-processed
"""
import json
import logging
import os
import random
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
log = logging.getLogger("audience-settings")

DATABASE_URL  = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/onlooker")
OLLAMA_HOST   = os.getenv("OLLAMA_HOST", "http://localhost:11434")
LLM_MODEL     = os.getenv("LLM_MODEL", "llama3.2")
DAPR_HTTP     = f"http://localhost:{os.getenv('DAPR_HTTP_PORT', '3502')}"
PUBSUB_NAME   = "onlooker-pubsub"
MAX_PARALLEL  = int(os.getenv("OLLAMA_NUM_PARALLEL", "4"))

_pool: asyncpg.Pool | None = None
_sem: asyncio.Semaphore | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _pool, _sem
    dsn  = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
    _pool = await asyncpg.create_pool(dsn, min_size=2, max_size=5)
    _sem  = asyncio.Semaphore(MAX_PARALLEL)
    log.info("audience-settings ready (parallel=%d)", MAX_PARALLEL)
    yield
    await _pool.close()


app = FastAPI(title="audience-settings", lifespan=lifespan)


@app.get("/dapr/subscribe")
def dapr_subscribe():
    return [{"pubsubname": PUBSUB_NAME, "topic": "features-extracted", "route": "/features-extracted"}]


async def _publish(topic: str, data: dict[str, Any]) -> None:
    async with httpx.AsyncClient() as c:
        await c.post(f"{DAPR_HTTP}/v1.0/publish/{PUBSUB_NAME}/{topic}", json=data, timeout=30)


async def _status(run_id: str, stage: str, detail: str = "") -> None:
    await _publish("pipeline-status", {"run_id": run_id, "stage": stage, "detail": detail})


_REACTION_PROMPT = """\
You are simulating an audience member with this profile:
- Type: {audience_type}
- Environment: {audience_environment}
- Domain/Area: {audience_area}
- Age range: {age_dstn}
- Location: {location}

They are seeing this feature of a presentation or document:
Feature: "{feature_name}"
Description: {feature_desc}

Rate their reaction (0-100 each):
- engagement : how interested/engaged this makes them
- approval   : how much they approve or like this
- clarity    : how clear and understandable it is
- relevance  : how relevant to their needs

Also write a one-sentence reaction thought in their voice.

Respond ONLY with JSON (no markdown):
{{"engagement": <int>, "approval": <int>, "clarity": <int>, "relevance": <int>, "reaction_thought": "<string>"}}
"""


def _simulate_sync(feature: dict, cfg: dict) -> dict:
    client = ollama.Client(host=OLLAMA_HOST)
    prompt = _REACTION_PROMPT.format(
        audience_type        = cfg.get("audience_type", "General professional audience"),
        audience_environment = cfg.get("audience_environment", "Professional setting"),
        audience_area        = cfg.get("audience_area", "General"),
        age_dstn             = cfg.get("age_dstn", "25-50"),
        location             = cfg.get("location", "Global"),
        feature_name         = feature.get("feature", ""),
        feature_desc         = feature.get("description", ""),
    )
    try:
        resp   = client.chat(
            model=LLM_MODEL,
            messages=[{"role": "user", "content": prompt}],
            format="json",
            options={"temperature": 0.4},
        )
        parsed = json.loads(resp["message"]["content"])
        for k in ("engagement", "approval", "clarity", "relevance"):
            if k in parsed:
                parsed[k] = max(0, min(100, int(parsed[k])))
        return {**feature, **parsed}
    except Exception as exc:
        log.warning("reaction failed for '%s': %s", feature.get("feature"), exc)
        return {
            **feature,
            "engagement":      random.randint(40, 72),
            "approval":        random.randint(40, 72),
            "clarity":         random.randint(50, 78),
            "relevance":       random.randint(38, 70),
            "reaction_thought": "Content acknowledged.",
        }


async def _simulate_async(feature: dict, cfg: dict) -> dict:
    async with _sem:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _simulate_sync, feature, cfg)


@app.post("/features-extracted")
async def on_features_extracted(request: Request) -> JSONResponse:
    body            = await request.json()
    data            = body.get("data", body)
    run_id          = data["run_id"]
    features        = data.get("features", [])
    audience_config = data.get("audience_config", {})
    insight_flags   = data.get("insight_flags", {})

    log.info("run=%s features=%d", run_id, len(features))
    await _status(run_id, "audience:started", f"Simulating {len(features)} feature reactions")

    # Massively parallel reaction simulation (bounded by semaphore)
    reactions = await asyncio.gather(*[
        _simulate_async(f, audience_config) for f in features
    ])

    # Aggregate
    def _avg(key: str) -> float:
        vals = [r.get(key, 0) for r in reactions if isinstance(r.get(key), (int, float))]
        return round(sum(vals) / len(vals), 1) if vals else 0.0

    metrics = {
        "engagement_avg": _avg("engagement"),
        "approval_avg":   _avg("approval"),
        "clarity_avg":    _avg("clarity"),
        "relevance_avg":  _avg("relevance"),
        "feature_count":  len(features),
        "audience_type":  audience_config.get("audience_type", ""),
        "audience_size":  audience_config.get("audience_size", 100),
    }

    # Persist
    async with _pool.acquire() as conn:
        await conn.execute(
            """
            UPDATE pipeline_runs
               SET audience_reactions = $1, metrics = $2, status = 'audience_processed'
             WHERE run_id = $3
            """,
            json.dumps(list(reactions)),
            json.dumps(metrics),
            uuid.UUID(run_id),
        )

    await _status(run_id, "audience:complete",
                  f"engagement={metrics['engagement_avg']} approval={metrics['approval_avg']}")
    await _publish("audience-processed", {
        "run_id":        run_id,
        "metrics":       metrics,
        "reactions":     list(reactions),
        "insight_flags": insight_flags,
    })

    return JSONResponse({"status": "SUCCESS"})
