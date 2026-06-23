import os
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["analyze"])

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
LLM_MODEL   = os.getenv("LLM_MODEL", "llama3.2")


class ChunkRequest(BaseModel):
    text: str
    session_id: str = "chat"
    persona_type: str = "executive"
    region: str = "us"
    focus_area: str = "business"
    environment: str = "professional"
    complexity: str = "medium"
    feedback_setting: str = "academic_us"
    audience_min_age: int = 18
    audience_max_age: int = 45
    audience_amount: int = 100


@router.post("/analyze/chunk")
async def analyze_chunk(req: ChunkRequest):
    """
    Quick chat-box analysis of a text chunk via Ollama.
    Returns a lightweight feedback event — for full pipeline analysis, use /document/upload.
    """
    events: list[dict] = []

    try:
        import ollama as _ollama
        client = _ollama.Client(host=OLLAMA_HOST)
        prompt = (
            f"You are a presentation coach for a {req.persona_type} audience "
            f"in a {req.environment} {req.focus_area} setting.\n\n"
            f"Analyze this content and give brief, actionable feedback:\n\n{req.text[:1500]}\n\n"
            "Return JSON with keys: "
            '"coaching_tip" (string), "clarity_score" (0-100), "engagement_score" (0-100), '
            '"key_strength" (string), "improvement" (string).'
        )
        resp = client.chat(
            model=LLM_MODEL,
            messages=[{"role": "user", "content": prompt}],
            format="json",
            options={"temperature": 0.3},
        )
        import json
        parsed = json.loads(resp["message"]["content"])
        events.append({"agent": "coaching", "payload": parsed})
    except Exception:
        # Ollama not available in local dev without Docker — return empty
        events.append({
            "agent": "coaching",
            "payload": {
                "coaching_tip":      "Analysis pending — start the Ollama service for live feedback.",
                "clarity_score":     0,
                "engagement_score":  0,
                "key_strength":      "",
                "improvement":       "",
            },
        })

    return {"events": events}
