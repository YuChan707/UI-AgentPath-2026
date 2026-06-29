"""embeding-service pipeline.

On a ``document.uploaded`` event:
  1. fetch the document bytes from Postgres by id,
  2. extract + clean + page-chunk the text,
  3. embed each chunk with Ollama,
  4. store the vectors in a per-product Chroma collection,
  5. emit progress/success to the UI over Dapr,
  6. hand off to features-extractor with the collection name.

Each step publishes a ``ServiceProgress`` heartbeat so the UI can show the
success state without ever touching an LLM itself.
"""

from __future__ import annotations

import logging

<<<<<<< HEAD
import db
import embed
from contracts import CollectionReady, DocumentUploaded, ServiceProgress
from dapr_io import publish
from extract import pages
=======
from dtos.messages import CollectionReady, DocumentUploaded, ServiceProgress

from . import db, embed
from .dapr_io import publish
from .extract import pages
>>>>>>> 15f913d (cleaning and restructuring to microservices infrastructure)

logger = logging.getLogger("embeding-service")

SERVICE = "embeding-service"
TOPIC_PROGRESS = "embedding.progress"
TOPIC_FEATURES = "features.extract"


async def _progress(id_product: str, event: str, detail: str = "", progress: float = 0.0) -> None:
    await publish(
        TOPIC_PROGRESS,
        ServiceProgress(id_product=id_product, service=SERVICE, event=event, detail=detail, progress=progress),
    )


async def process(message: DocumentUploaded) -> None:
    """Run the full embedding pipeline for one uploaded product document."""
    pid = message.id_product
    logger.info("processing product %s (%s)", pid, message.doc_type)
    await _progress(pid, "started", f"doc_type={message.doc_type}")

    product = await db.fetch_product(pid)
    if product is None:
        await _progress(pid, "error", "product not found / empty content")
        logger.warning("product %s not found", pid)
        return

    # 1) extract + clean + page-chunk
    chunks = pages(product.content, product.doc_type or message.doc_type)
    if not chunks:
        await _progress(pid, "error", "no text extracted")
        logger.warning("no text extracted for %s", pid)
        return
    await _progress(pid, "progress", f"{len(chunks)} chunks extracted", 0.33)

    # 2) embed with Ollama
    await db.set_collection(pid, embed.collection_name(pid), status="embedding")
    vectors = await embed.embed_chunks(chunks)
    await _progress(pid, "progress", f"{len(vectors)} chunks embedded", 0.66)

    # 3) store vectors in Chroma
    collection = embed.store(pid, chunks, vectors)
    await db.set_collection(pid, collection, status="embedded")
    await _progress(pid, "success", f"collection {collection} ready ({len(chunks)} chunks)", 1.0)
    logger.info("product %s embedded into %s (%d chunks)", pid, collection, len(chunks))

    # 4) hand off to features-extractor
    await publish(
        TOPIC_FEATURES,
        CollectionReady(id_product=pid, collection=collection, n_chunks=len(chunks)),
    )


__all__ = ["process", "TOPIC_PROGRESS", "TOPIC_FEATURES"]
