"""Publish events to the Dapr sidecar over HTTP (no gRPC SDK needed)."""

from __future__ import annotations

import os

import httpx
from pydantic import BaseModel

DAPR_HTTP_PORT = os.getenv("DAPR_HTTP_PORT", "3500")
PUBSUB_NAME = os.getenv("PUBSUB_NAME", "pubsub")

_BASE = f"http://localhost:{DAPR_HTTP_PORT}/v1.0/publish/{PUBSUB_NAME}"


async def publish(topic: str, payload: BaseModel | dict) -> None:
    """Publish a message to a Dapr pub/sub topic. Best-effort (never raises)."""
    body = payload.model_dump() if isinstance(payload, BaseModel) else payload
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(f"{_BASE}/{topic}", json=body)
            resp.raise_for_status()
    except Exception as exc:  # noqa: BLE001 - telemetry, must not break the pipeline
        print(f"[dapr] publish to {topic} failed: {type(exc).__name__}: {exc}")


__all__ = ["publish", "PUBSUB_NAME"]
