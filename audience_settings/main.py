"""Dapr subscriber for audience-settings.

Subscribes to ``features.ready``. For each (audience group x product feature) it
runs the UiPath/LangGraph reaction agent (local Ollama) to produce the seven
AudienceResponse scores, persists them, then hands off to develop-analysis via
``audience.ready``.

Parallelism is bounded by OLLAMA_NUM_PARALLEL (defaults to the available CPUs) so
we don't overwhelm the local Ollama with concurrent generations.

Run with a Dapr sidecar (from this folder):
    export REDIS_HOST=localhost:6379
    dapr run --app-id audience-settings --app-port 8102 \
        --resources-path components \
        -- uvicorn main:app --host 0.0.0.0 --port 8102
"""

from __future__ import annotations

import asyncio
import logging
import os

from fastapi import FastAPI, Request

import db
from agent import graph
from contracts import AudienceReady, FeaturesReady, ServiceProgress
from dapr_io import publish
from groups import build_groups

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("audience-settings")

app = FastAPI(title="audience-settings", version="0.1.0")

PUBSUB_NAME = os.getenv("PUBSUB_NAME", "pubsub")
SERVICE = "audience-settings"
TOPIC_IN = "features.ready"
TOPIC_PROGRESS = "embedding.progress"
TOPIC_OUT = "audience.ready"

# Dynamic concurrency: scale to the box, override with OLLAMA_NUM_PARALLEL.
_NUM_PARALLEL = int(os.getenv("OLLAMA_NUM_PARALLEL") or max(2, os.cpu_count() or 2))


@app.get("/dapr/subscribe")
def subscribe() -> list[dict]:
    return [{"pubsubname": PUBSUB_NAME, "topic": TOPIC_IN, "route": "/events/features-ready"}]


async def _progress(id_product: str, event: str, detail: str = "", progress: float = 0.0) -> None:
    await publish(
        TOPIC_PROGRESS,
        ServiceProgress(id_product=id_product, service=SERVICE, event=event, detail=detail, progress=progress),
    )


@app.post("/events/features-ready")
async def on_features_ready(request: Request) -> dict:
    body = await request.json()
    msg = FeaturesReady(**body.get("data", body))
    pid = msg.id_product
    logger.info("reacting audience for %s", pid)
    await _progress(pid, "started")

    data = await db.fetch_input(pid)
    if not data or not data.features:
        await _progress(pid, "error", "no features to react to")
        return {"status": "SUCCESS"}

    groups = build_groups(data.settings)
    pairs = [(g, f) for g in groups for f in data.features]
    sem = asyncio.Semaphore(_NUM_PARALLEL)

    async def react(group: dict, feature: dict) -> dict:
        async with sem:
            result = await graph.ainvoke({"group": group, "feature": feature})
        return {
            "id_audience": group.get("id_audience", "group"),
            "id_feature": feature.get("feature_id", "feature"),
            "scores": result.get("scores") or {},
        }

    rows = await asyncio.gather(*(react(g, f) for g, f in pairs))
    await db.save_responses(pid, rows)
    await _progress(pid, "success", f"{len(rows)} reactions ({len(groups)} groups x {len(data.features)} features)", 1.0)
    await publish(TOPIC_OUT, AudienceReady(id_product=pid, n_features=len(data.features), n_groups=len(groups)))
    logger.info("product %s -> %d audience responses", pid, len(rows))
    return {"status": "SUCCESS"}


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": SERVICE}
