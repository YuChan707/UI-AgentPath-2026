"""Persist the extracted features into products.features (asyncpg)."""

from __future__ import annotations

import json
import os

import asyncpg


def _dsn() -> str:
    url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/onlooker")
    if "+asyncpg" in url:
        url = url.replace("+asyncpg", "")
    if url.startswith("postgresql+"):
        url = "postgresql://" + url.split("://", 1)[1]
    return url


async def save_features(id_product: str, features: list[dict]) -> None:
    """Write the features JSON and advance the product status."""
    conn = await asyncpg.connect(dsn=_dsn())
    try:
        await conn.execute(
            "UPDATE products SET features = $2::jsonb, status = 'extracted' WHERE id_product = $1",
            id_product,
            json.dumps(features),
        )
    finally:
        await conn.close()


__all__ = ["save_features"]
