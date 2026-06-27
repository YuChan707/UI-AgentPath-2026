"""Aggregate audience_responses and persist the final product_analysis (asyncpg)."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass

import asyncpg

_SCORE_COLS = (
    "confident_score",
    "complexity_score",
    "security_score",
    "engagement_score",
    "interest_score",
    "value_perceived_score",
    "general_sentiment_score",
)


def _dsn() -> str:
    url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/onlooker")
    if "+asyncpg" in url:
        url = url.replace("+asyncpg", "")
    if url.startswith("postgresql+"):
        url = "postgresql://" + url.split("://", 1)[1]
    return url


@dataclass
class AnalysisInput:
    features: list
    insights: dict
    aggregate: dict  # avg per score metric, as a 0-100 percentage


async def fetch_input(id_product: str) -> AnalysisInput | None:
    avg_cols = ", ".join(f"avg({c}) AS {c}" for c in _SCORE_COLS)
    conn = await asyncpg.connect(dsn=_dsn())
    try:
        prod = await conn.fetchrow(
            "SELECT features, insights FROM products WHERE id_product = $1", id_product
        )
        agg = await conn.fetchrow(
            f"SELECT {avg_cols} FROM audience_responses WHERE id_product = $1", id_product
        )
    finally:
        await conn.close()
    if not prod:
        return None
    features = prod["features"] or []
    if isinstance(features, str):
        features = json.loads(features)
    insights = prod["insights"] or {}
    if isinstance(insights, str):
        insights = json.loads(insights)
    aggregate = {
        c: round(float(agg[c]) * 100, 1) if agg and agg[c] is not None else None
        for c in _SCORE_COLS
    }
    return AnalysisInput(features=features, insights=insights, aggregate=aggregate)


async def save_analysis(id_product: str, analysis: dict, aggregate: dict) -> None:
    conn = await asyncpg.connect(dsn=_dsn())
    try:
        async with conn.transaction():
            await conn.execute(
                """
                INSERT INTO product_analysis (
                    id_product, strengths, weakness, points_with_potential,
                    audience_response_analysis, final_recomendations, aggregate_scores
                ) VALUES ($1, $2::jsonb, $3::jsonb, $4::jsonb, $5, $6::jsonb, $7::jsonb)
                ON CONFLICT (id_product) DO UPDATE SET
                    strengths = EXCLUDED.strengths,
                    weakness = EXCLUDED.weakness,
                    points_with_potential = EXCLUDED.points_with_potential,
                    audience_response_analysis = EXCLUDED.audience_response_analysis,
                    final_recomendations = EXCLUDED.final_recomendations,
                    aggregate_scores = EXCLUDED.aggregate_scores
                """,
                id_product,
                json.dumps(analysis.get("strengths")),
                json.dumps(analysis.get("weakness")),
                json.dumps(analysis.get("points_with_potential")),
                analysis.get("audience_response_analysis"),
                json.dumps(analysis.get("final_recomendations")),
                json.dumps(aggregate),
            )
            await conn.execute(
                "UPDATE products SET status = 'analyzed' WHERE id_product = $1", id_product
            )
    finally:
        await conn.close()


__all__ = ["AnalysisInput", "fetch_input", "save_analysis"]
