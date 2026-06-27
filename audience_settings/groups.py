"""Derive the audience groups to simulate from the user's AudienceSettings.

The UI's settings configure WHO reacts. Empty values fall back to the documented
defaults (globalized / generic / 20-45 / ~1500). For the scaffold we expand the
gender distribution into a small, representative set of groups; this can grow to
the statistical groups produced by data_processor later.
"""

from __future__ import annotations


def build_groups(settings: dict | None) -> list[dict]:
    s = settings or {}
    audience_type = s.get("audience_type") or "globalized"
    environment = s.get("audience_enviroment") or "globalized"
    area = s.get("audience_area") or "globalized"
    age = s.get("age_dstn") or "20-45"
    size = s.get("audience_size") or 1500
    gender = (s.get("gender_dstn") or "generic").lower()

    if gender in ("male", "oriented to male"):
        genders = ["male"]
    elif gender in ("female", "oriented to female"):
        genders = ["female"]
    else:
        genders = ["male", "female", "non_binary"]

    base = {
        "audience_type": audience_type,
        "environment": environment,
        "area": area,
        "age_range": age,
        "size": size,
    }
    return [
        {**base, "id_audience": f"{audience_type}-{g}-{age}", "gender": g}
        for g in genders
    ]


__all__ = ["build_groups"]
