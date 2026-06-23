"""
features-extractor
  Subscribes: embedding-complete
  Publishes:  features-extracted, pipeline-status

Pipeline step 2 of 4:
  query ChromaDB vectors
  → LLM (llama3.2) identifies 8-12 key content features
  → persist to pipeline_runs.features
  → publish features-extracted
"""
import json
import logging
import os
import asyncio
import re
from contextlib import asynccontextmanager
from typing import Any
import uuid

import asyncpg
import chromadb
import httpx
import ollama
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("features-extractor")

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/onlooker")
CHROMA_HOST  = os.getenv("CHROMA_HOST", "localhost")
CHROMA_PORT  = int(os.getenv("CHROMA_PORT", "8000"))
OLLAMA_HOST  = os.getenv("OLLAMA_HOST", "http://localhost:11434")
LLM_MODEL    = os.getenv("LLM_MODEL", "llama3.2")
DAPR_HTTP    = f"http://localhost:{os.getenv('DAPR_HTTP_PORT', '3501')}"
PUBSUB_NAME  = "onlooker-pubsub"

_pool: asyncpg.Pool | None = None
_chroma: chromadb.HttpClient | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _pool, _chroma
    dsn = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
    _pool   = await asyncpg.create_pool(dsn, min_size=2, max_size=5)
    _chroma = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)
    log.info("features-extractor ready")
    yield
    await _pool.close()


app = FastAPI(title="features-extractor", lifespan=lifespan)


@app.get("/dapr/subscribe")
def dapr_subscribe():
    return [{"pubsubname": PUBSUB_NAME, "topic": "embedding-complete", "route": "/embedding-complete"}]


async def _publish(topic: str, data: dict[str, Any]) -> None:
    async with httpx.AsyncClient() as c:
        await c.post(f"{DAPR_HTTP}/v1.0/publish/{PUBSUB_NAME}/{topic}", json=data, timeout=30)


async def _status(run_id: str, stage: str, detail: str = "") -> None:
    await _publish("pipeline-status", {"run_id": run_id, "stage": stage, "detail": detail})


_EXTRACTION_PROMPT = """\
You are analyzing document content to identify key presentational and persuasive features.

Document excerpts:
{text_sample}

Identify exactly 8-12 distinct features of this content. A feature is a notable characteristic,
claim, topic, structural element, or narrative choice.

Return a JSON array. Each item must have:
  "feature"     : short label (3-7 words)
  "description" : one sentence
  "importance"  : integer 1-10

Example:
[
  {{"feature": "Strong ROI Claims", "description": "Makes specific quantified return-on-investment claims.", "importance": 9}},
  {{"feature": "Technical Jargon", "description": "Heavy domain-specific terminology throughout.", "importance": 6}}
]

Return ONLY the JSON array — no preamble, no markdown fences.
"""


def _extract_features_sync(text_sample: str) -> list[dict]:
    client = ollama.Client(host=OLLAMA_HOST)
    resp   = client.chat(
        model=LLM_MODEL,
        messages=[{"role": "user", "content": _EXTRACTION_PROMPT.format(text_sample=text_sample[:4000])}],
        format="json",
        options={"temperature": 0.2},
    )
    raw = resp["message"]["content"]
    try:
        parsed = json.loads(raw)
        return parsed if isinstance(parsed, list) else []
    except json.JSONDecodeError:
        m = re.search(r"\[.*?\]", raw, re.DOTALL)
        if m:
            try:
                return json.loads(m.group())
            except Exception:
                pass
    return [{"feature": "General Content", "description": "Document analyzed.", "importance": 5}]


@app.post("/embedding-complete")
async def on_embedding_complete(request: Request) -> JSONResponse:
    body            = await request.json()
    data            = body.get("data", body)
    run_id          = data["run_id"]
    collection_name = data["collection_name"]
    audience_config = data.get("audience_config", {})
    insight_flags   = data.get("insight_flags", {})

    log.info("run=%s collection=%s", run_id, collection_name)
    await _status(run_id, "features:started", "Querying vector database")

    # 1 — Sample documents from ChromaDB
    col     = _chroma.get_collection(collection_name)
    results = col.get(limit=10, include=["documents"])
    docs    = results.get("documents") or []
    sample  = "\n\n---\n\n".join(docs[:8])

    # 2 — LLM extraction
    await _status(run_id, "features:extracting", "LLM analyzing content structure")
    loop     = asyncio.get_event_loop()
    features = await loop.run_in_executor(None, _extract_features_sync, sample)

    # 3 — Persist
    async with _pool.acquire() as conn:
        await conn.execute(
            "UPDATE pipeline_runs SET features = $1, status = 'features_extracted' WHERE run_id = $2",
            json.dumps(features),
            uuid.UUID(run_id),
        )

    # 4 — Next stage
    await _status(run_id, "features:complete", f"Extracted {len(features)} features")
    await _publish("features-extracted", {
        "run_id":         run_id,
        "features":       features,
        "audience_config": audience_config,
        "insight_flags":  insight_flags,
    })

    return JSONResponse({"status": "SUCCESS"})
