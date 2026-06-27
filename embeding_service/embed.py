"""Embed page chunks with a local Ollama embedding model and store the vectors
in ChromaDB.

The model does the embeddings (not Chroma) — we pass precomputed vectors to the
collection, exactly as the flow specifies ("convierte a embedding los chunks
usando ollama para almacenar los vectores en chroma db").
"""

from __future__ import annotations

import asyncio
import os

import httpx

# Native Ollama API base (no /v1). The embeddings endpoint is /api/embeddings.
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434").rstrip("/")
OLLAMA_EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")

CHROMA_HOST = os.getenv("CHROMA_HOST", "localhost")
CHROMA_PORT = int(os.getenv("CHROMA_PORT", "8000"))

# Dynamic concurrency for the local Ollama (defaults to CPU count). Bounds how
# many embedding requests are in flight at once so we don't overwhelm the model.
NUM_PARALLEL = int(os.getenv("OLLAMA_NUM_PARALLEL") or max(2, os.cpu_count() or 2))


def collection_name(id_product: str) -> str:
    """Deterministic Chroma collection name for a product."""
    return f"product_{id_product.replace('-', '')}"


async def embed_chunks(chunks: list[str]) -> list[list[float]]:
    """Return one embedding vector per chunk via the Ollama embeddings API.

    Runs the calls **concurrently** (bounded by ``OLLAMA_NUM_PARALLEL``) and
    preserves input order via ``asyncio.gather``.
    """
    sem = asyncio.Semaphore(NUM_PARALLEL)
    async with httpx.AsyncClient(timeout=120) as client:
        async def _one(chunk: str) -> list[float]:
            async with sem:
                resp = await client.post(
                    f"{OLLAMA_HOST}/api/embeddings",
                    json={"model": OLLAMA_EMBED_MODEL, "prompt": chunk},
                )
                resp.raise_for_status()
                return resp.json()["embedding"]

        return list(await asyncio.gather(*(_one(c) for c in chunks)))


def store(id_product: str, chunks: list[str], vectors: list[list[float]]) -> str:
    """Create/replace the product's Chroma collection with the chunk vectors."""
    import chromadb

    client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)
    name = collection_name(id_product)
    # Idempotent: drop a previous run's collection so re-embedding is clean.
    try:
        client.delete_collection(name)
    except Exception:
        pass
    collection = client.create_collection(name, metadata={"hnsw:space": "cosine"})
    collection.add(
        ids=[f"{id_product}_p{i}" for i in range(len(chunks))],
        documents=chunks,
        embeddings=vectors,
        metadatas=[{"id_product": id_product, "page": i} for i in range(len(chunks))],
    )
    return name


__all__ = ["embed_chunks", "store", "collection_name"]
