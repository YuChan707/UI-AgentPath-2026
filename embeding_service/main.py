"""Dapr subscriber for the embeding-service.

Subscribes to ``document.uploaded`` and runs the embedding pipeline. The UI
publishes the event; this service does the heavy lifting (extraction +
embeddings + Chroma) and reports progress back over Dapr.

<<<<<<< HEAD
Run with a Dapr sidecar (from this folder):
    export REDIS_HOST=localhost:6379
    dapr run --app-id embeding-service --app-port 8100 \
        --resources-path components \
        -- uvicorn main:app --host 0.0.0.0 --port 8100
=======
Run with a Dapr sidecar:
    dapr run --app-id embeding-service --app-port 8100 \
        --resources-path embeding_service/components \
        -- uvicorn embeding_service.main:app --host 0.0.0.0 --port 8100
>>>>>>> 15f913d (cleaning and restructuring to microservices infrastructure)
"""

from __future__ import annotations

import logging
import os

from fastapi import FastAPI, Request

<<<<<<< HEAD
import pipeline
from contracts import DocumentUploaded
=======
from dtos.messages import DocumentUploaded

from . import pipeline
>>>>>>> 15f913d (cleaning and restructuring to microservices infrastructure)

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

app = FastAPI(title="embeding-service", version="0.1.0")

PUBSUB_NAME = os.getenv("PUBSUB_NAME", "pubsub")
TOPIC_DOCUMENT_UPLOADED = "document.uploaded"


@app.get("/dapr/subscribe")
def subscribe() -> list[dict]:
    """Declarative subscription Dapr reads on startup."""
    return [
        {
            "pubsubname": PUBSUB_NAME,
            "topic": TOPIC_DOCUMENT_UPLOADED,
            "route": "/events/document-uploaded",
        }
    ]


@app.post("/events/document-uploaded")
async def on_document_uploaded(request: Request) -> dict:
    """Handle a document.uploaded event (CloudEvent-wrapped by Dapr)."""
    body = await request.json()
    data = body.get("data", body)  # unwrap the CloudEvent envelope
    message = DocumentUploaded(**data)
    await pipeline.process(message)
    return {"status": "SUCCESS"}


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "embeding-service"}
