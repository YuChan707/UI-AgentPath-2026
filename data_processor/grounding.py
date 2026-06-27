"""Local grounding over the REAL Census statistics (no external service).

Anchors the synthetic generation in the real statistics of the location so the
model reasons over evidence instead of inventing in a vacuum. It is a
self-contained, offline grounding built from the data the ingestor already
produced (Census ACS5) — no external retrieval service.

`ground(location_stats)` returns a text block ready to append to the model's
prompt.
"""

from __future__ import annotations


def ground(location_stats: dict | None = None) -> str:
    """Return a grounding block (text) to append to the prompt."""
    facts = _facts(location_stats)
    if not facts:
        return ""
    body = "\n".join(f"- {p}" for p in facts)
    return (
        "GROUNDING EVIDENCE (real Census statistics — use as facts, do not "
        f"contradict):\n{body}"
    )


def _facts(location_stats: dict | None) -> list[str]:
    if not location_stats:
        return []
    s = location_stats
    facts: list[str] = []
    if s.get("median_income") is not None:
        facts.append(f"Real median household income: ${s['median_income']} (Census ACS5).")
    if s.get("unemployment_rate") is not None:
        facts.append(f"Real unemployment rate: {s['unemployment_rate']}%.")
    if s.get("poverty_rate") is not None:
        facts.append(f"Real poverty rate: {s['poverty_rate']}%.")
    if s.get("ethnicity_distribution"):
        top = sorted(s["ethnicity_distribution"].items(), key=lambda kv: kv[1], reverse=True)
        dist = ", ".join(f"{k} {v:.1f}%" for k, v in top if v)
        facts.append(f"Real ethnic distribution: {dist}.")
    if s.get("age_ranges"):
        ages = ", ".join(f"{k} {v:.1f}%" for k, v in s["age_ranges"].items())
        facts.append(f"Real age distribution: {ages}.")
    if s.get("avg_education") is not None:
        facts.append(f"Real education indicator (% bachelor+): {s['avg_education']}.")
    return facts


__all__ = ["ground"]
