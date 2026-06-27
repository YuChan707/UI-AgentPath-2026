"""Dapr subscriber for develop-analysis.

Subscribes to ``audience.ready``. Aggregates the audience reactions, runs the
UiPath/LangGraph analysis agent (local Ollama) to produce the user-selected
insights, persists them, and signals the UI via ``analysis.ready``.

Run with a Dapr sidecar (from this folder):
    export REDIS_HOST=localhost:6379
    dapr run --app-id develop-analysis --app-port 8103 \
        --resources-path components \
        -- uvicorn main:app --host 0.0.0.0 --port 8103
"""

from __future__ import annotations

import logging
import os

from fastapi import FastAPI, Request

import db
from agent import graph
from contracts import AnalysisReady, AudienceReady, ServiceProgress
from dapr_io import publish

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("develop-analysis")

app = FastAPI(title="develop-analysis", version="0.1.0")

PUBSUB_NAME = os.getenv("PUBSUB_NAME", "pubsub")
SERVICE = "develop-analysis"
TOPIC_IN = "audience.ready"
TOPIC_PROGRESS = "embedding.progress"
TOPIC_OUT = "analysis.ready"


@app.get("/dapr/subscribe")
def subscribe() -> list[dict]:
    return [{"pubsubname": PUBSUB_NAME, "topic": TOPIC_IN, "route": "/events/audience-ready"}]


async def _progress(id_product: str, event: str, detail: str = "", progress: float = 0.0) -> None:
    await publish(
        TOPIC_PROGRESS,
        ServiceProgress(id_product=id_product, service=SERVICE, event=event, detail=detail, progress=progress),
    )


@app.post("/events/audience-ready")
async def on_audience_ready(request: Request) -> dict:
    body = await request.json()
    msg = AudienceReady(**body.get("data", body))
    pid = msg.id_product
    logger.info("analyzing %s", pid)
    await _progress(pid, "started")

    data = await db.fetch_input(pid)
    if not data:
        await _progress(pid, "error", "product not found")
        return {"status": "SUCCESS"}

    result = await graph.ainvoke(
        {"features": data.features, "aggregate": data.aggregate, "insights": data.insights},
    )
    analysis = result.get("analysis") or {}

    await db.save_analysis(pid, analysis, data.aggregate)
    sections = [k for k in ("strengths", "weakness", "points_with_potential", "audience_response_analysis") if analysis.get(k)]
    await _progress(pid, "success", f"insights: {', '.join(sections) or 'none'}", 1.0)
    await publish(TOPIC_OUT, AnalysisReady(id_product=pid, insights=sections))
    logger.info("product %s analyzed -> %s", pid, sections)
    return {"status": "SUCCESS"}


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": SERVICE}
