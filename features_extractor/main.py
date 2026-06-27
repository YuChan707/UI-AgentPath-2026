"""Dapr subscriber for features-extractor.

Subscribes to ``features.extract`` (emitted by embeding-service when a product's
Chroma collection is ready). Runs the UiPath/LangGraph agent against the local
Ollama model to extract the product's features, persists them, and hands off to
audience-settings via ``features.ready``.

Run with a Dapr sidecar (from this folder):
    export REDIS_HOST=localhost:6379
    dapr run --app-id features-extractor --app-port 8101 \
        --resources-path components \
        -- uvicorn main:app --host 0.0.0.0 --port 8101
"""

from __future__ import annotations

import asyncio
import logging
import os

from fastapi import FastAPI, Request

import chroma_io
import db
from agent import graph
from contracts import CollectionReady, FeaturesReady, ServiceProgress
from dapr_io import publish

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("features-extractor")

app = FastAPI(title="features-extractor", version="0.1.0")

PUBSUB_NAME = os.getenv("PUBSUB_NAME", "pubsub")
SERVICE = "features-extractor"
TOPIC_IN = "features.extract"
TOPIC_PROGRESS = "embedding.progress"   # shared UI progress topic
TOPIC_OUT = "features.ready"


@app.get("/dapr/subscribe")
def subscribe() -> list[dict]:
    return [{"pubsubname": PUBSUB_NAME, "topic": TOPIC_IN, "route": "/events/features-extract"}]


async def _progress(id_product: str, event: str, detail: str = "", progress: float = 0.0) -> None:
    await publish(
        TOPIC_PROGRESS,
        ServiceProgress(id_product=id_product, service=SERVICE, event=event, detail=detail, progress=progress),
    )


@app.post("/events/features-extract")
async def on_features_extract(request: Request) -> dict:
    body = await request.json()
    msg = CollectionReady(**body.get("data", body))
    pid, collection = msg.id_product, msg.collection
    logger.info("extracting features for %s from %s", pid, collection)
    await _progress(pid, "started", f"collection={collection}")

    # Chroma's client is sync — keep that single call off the event loop.
    chunks = await asyncio.to_thread(chroma_io.get_chunks, collection)
    if not chunks:
        await _progress(pid, "error", "empty collection")
        return {"status": "SUCCESS"}

    # Run the UiPath/LangGraph agent natively async (Ollama via ainvoke).
    result = await graph.ainvoke({"collection": collection, "chunks": chunks})
    features = result.get("features") or []

    await db.save_features(pid, features)
    await _progress(pid, "success", f"{len(features)} features extracted", 1.0)
    await publish(TOPIC_OUT, FeaturesReady(id_product=pid, collection=collection, n_features=len(features)))
    logger.info("product %s -> %d features", pid, len(features))
    return {"status": "SUCCESS"}


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": SERVICE}
