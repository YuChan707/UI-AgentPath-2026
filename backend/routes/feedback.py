import os
import json
from typing import Annotated

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(tags=["feedback"])

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
LLM_MODEL   = os.getenv("LLM_MODEL", "llama3.2")

# Feedback persona definitions — previously lived in agents/feedback.py
FEEDBACK_SETTINGS: dict[str, dict] = {
    "academic_us": {
        "group":                "academic",
        "location":             "United States",
        "culture":              "Western",
        "communication_style":  "Evidence-based, data-driven",
        "values":               "Rigor, citations, peer review",
        "concerns":             ["methodology", "statistical validity", "reproducibility"],
    },
    "academic_europe": {
        "group":                "academic",
        "location":             "Europe",
        "culture":              "Western",
        "communication_style":  "Theoretical, philosophical",
        "values":               "Depth, nuance, historical context",
        "concerns":             ["theoretical framework", "critical analysis", "interdisciplinary perspective"],
    },
    "business_uk": {
        "group":                "business",
        "location":             "United Kingdom",
        "culture":              "Western",
        "communication_style":  "Formal, diplomatic, understated",
        "values":               "Professionalism, tradition, measured risk",
        "concerns":             ["ROI", "regulatory compliance", "long-term stability"],
    },
    "business_asia": {
        "group":                "business",
        "location":             "Asia",
        "culture":              "Eastern",
        "communication_style":  "Relationship-focused, indirect",
        "values":               "Consensus, trust, face-saving",
        "concerns":             ["relationship building", "cultural sensitivity", "long-term partnership"],
    },
    "startup": {
        "group":                "business",
        "location":             "Global",
        "culture":              "Innovation",
        "communication_style":  "Direct, high-energy, data-backed",
        "values":               "Disruption, speed, scalability",
        "concerns":             ["market size", "competitive moat", "growth trajectory"],
    },
    "community": {
        "group":                "community",
        "location":             "Diverse",
        "culture":              "Multicultural",
        "communication_style":  "Accessible, inclusive, practical",
        "values":               "Equity, accessibility, real-world impact",
        "concerns":             ["practical impact", "inclusivity", "community benefit"],
    },
}

_FEEDBACK_PROMPT = """\
You are simulating a feedback reviewer from the following perspective:
- Location: {location}
- Culture: {culture}
- Group: {group}
- Communication style: {communication_style}
- Core values: {values}
- Key concerns: {concerns}

Evaluate this content:
\"\"\"{text}\"\"\"

Context:
- Complexity level: {complexity}
- Environment: {environment}

Provide feedback as this persona. Return ONLY JSON with these exact keys:
{{
  "feedback_type": "critique" | "praise" | "neutral",
  "relevance_score": <integer 1-10>,
  "key_concern": "<one main concern from your perspective>",
  "critical_question": "<one question this persona would ask>",
  "cultural_note": "<cultural observation, or null if none>",
  "recommendation": "<one actionable recommendation>",
  "alignment_with_values": "<how well content aligns with this persona's values>"
}}
"""


def get_available_feedback_settings() -> dict:
    return FEEDBACK_SETTINGS


class FeedbackRequest(BaseModel):
    text: str
    feedback_setting: str = "academic_us"
    complexity: str = "medium"
    environment: str = "professional"


@router.get("/feedback/settings")
def get_feedback_settings():
    return get_available_feedback_settings()


@router.post(
    "/feedback/generate",
    responses={400: {"description": "Text too short or unknown feedback_setting"}},
)
async def generate_feedback(request: FeedbackRequest):
    if not request.text or len(request.text.strip()) < 5:
        raise HTTPException(status_code=400, detail="Text must be at least 5 characters")

    cfg = FEEDBACK_SETTINGS.get(request.feedback_setting)
    if not cfg:
        raise HTTPException(status_code=400, detail=f"Unknown feedback_setting: {request.feedback_setting}")

    prompt = _FEEDBACK_PROMPT.format(
        location             = cfg["location"],
        culture              = cfg["culture"],
        group                = cfg["group"],
        communication_style  = cfg["communication_style"],
        values               = cfg["values"],
        concerns             = ", ".join(cfg["concerns"]),
        text                 = request.text[:2000],
        complexity           = request.complexity,
        environment          = request.environment,
    )

    try:
        import ollama
        client = ollama.Client(host=OLLAMA_HOST)
        resp   = client.chat(
            model=LLM_MODEL,
            messages=[{"role": "user", "content": prompt}],
            format="json",
            options={"temperature": 0.35},
        )
        payload = json.loads(resp["message"]["content"])
    except Exception as exc:
        # Ollama unavailable (local dev without Docker) — return a placeholder
        payload = {
            "feedback_type":         "neutral",
            "relevance_score":        5,
            "key_concern":           "Analysis unavailable — start Ollama to get live feedback.",
            "critical_question":     "",
            "cultural_note":         None,
            "recommendation":        "Ensure the Ollama service is running with the llama3.2 model.",
            "alignment_with_values": str(exc),
        }

    return {
        **payload,
        "setting":  request.feedback_setting,
        "group":    cfg["group"],
        "location": cfg["location"],
        "culture":  cfg["culture"],
    }


@router.get("/feedback/available-perspectives")
def get_available_perspectives():
    organized: dict[str, dict] = {"academic": {}, "business": {}, "community": {}}
    for key, cfg in FEEDBACK_SETTINGS.items():
        group = cfg["group"]
        if group in organized:
            organized[group][key] = {
                "label":    f"{cfg['location']} — {cfg['culture']}",
                "location": cfg["location"],
                "culture":  cfg["culture"],
                "key":      key,
            }
    return organized
