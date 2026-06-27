"""Read the uploaded product document from Postgres by id.

The UI stores the raw file in the ``products`` table; this service only
receives the id over Dapr and fetches the bytes here. Uses asyncpg directly —
a single query, no ORM needed.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

import asyncpg


def _dsn() -> str:
    """Return a plain ``postgres://`` DSN for asyncpg (strips SQLAlchemy driver)."""
    url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/onlooker")
    # asyncpg wants postgres://, not postgresql+asyncpg://
    if "+asyncpg" in url:
        url = url.replace("+asyncpg", "")
    if url.startswith("postgresql+"):
        url = "postgresql://" + url.split("://", 1)[1]
    return url


@dataclass
class Product:
    id_product: str
    document_name: str
    doc_type: str
    content: bytes


async def fetch_product(id_product: str) -> Product | None:
    """Fetch a product's document bytes + metadata by id. None if not found."""
    conn = await asyncpg.connect(dsn=_dsn())
    try:
        row = await conn.fetchrow(
            "SELECT id_product, document_name, doc_type, content "
            "FROM products WHERE id_product = $1",
            id_product,
        )
    finally:
        await conn.close()
    if not row or row["content"] is None:
        return None
    return Product(
        id_product=str(row["id_product"]),
        document_name=row["document_name"],
        doc_type=(row["doc_type"] or "").lower().lstrip("."),
        content=bytes(row["content"]),
    )


async def set_collection(id_product: str, collection: str, status: str) -> None:
    """Persist the chroma collection name + advance the product status."""
    conn = await asyncpg.connect(dsn=_dsn())
    try:
        await conn.execute(
            "UPDATE products SET collection = $2, status = $3 WHERE id_product = $1",
            id_product, collection, status,
        )
    finally:
        await conn.close()


__all__ = ["Product", "fetch_product", "set_collection"]
