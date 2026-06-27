"""Read the product's chunks from its ChromaDB collection."""

from __future__ import annotations

import os


def get_chunks(collection: str, limit: int = 200) -> list[str]:
    """Return the stored document chunks of a Chroma collection."""
    import chromadb

    client = chromadb.HttpClient(
        host=os.getenv("CHROMA_HOST", "localhost"),
        port=int(os.getenv("CHROMA_PORT", "8000")),
    )
    col = client.get_collection(collection)
    res = col.get(include=["documents"], limit=limit)
    return res.get("documents") or []


__all__ = ["get_chunks"]
