"""audience-settings agent.

A LangGraph agent (UiPath Python Agent SDK / uipath-langchain) that simulates how
one audience group reacts to one product feature, returning the seven scores of
the AudienceResponse entity. Local Ollama model, no cloud.

Prompt origin: agent_prompts/audience_reaction.md + data_processor REACTION_PROMPT.
"""

from __future__ import annotations

import json
import os
from typing import TypedDict

from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1")

SCORE_KEYS = (
    "confident_score",
    "complexity_score",
    "security_score",
    "engagement_score",
    "interest_score",
    "value_perceived_score",
    "general_sentiment_score",
)

SYSTEM = (
    "You simulate a specific AUDIENCE GROUP reacting to a digital product FEATURE. "
    "Anchor to the group's profile; do not invent. Return ONLY valid JSON with these "
    "float fields in [0,1]: " + ", ".join(SCORE_KEYS) + ". No prose, no markdown."
)


class State(TypedDict, total=False):
    group: dict
    feature: dict
    scores: dict


def _llm() -> ChatOpenAI:
    return ChatOpenAI(
        base_url=OLLAMA_BASE_URL,
        api_key=os.getenv("OLLAMA_API_KEY", "ollama"),
        model=OLLAMA_MODEL,
        temperature=0.3,
    )


def _parse_scores(text: str) -> dict:
    text = (text or "").strip().replace("```json", "").replace("```", "").strip()
    try:
        data = json.loads(text)
    except Exception:
        i, j = text.find("{"), text.rfind("}")
        data = json.loads(text[i : j + 1]) if i != -1 and j != -1 else {}
    out = {}
    for k in SCORE_KEYS:
        v = data.get(k) if isinstance(data, dict) else None
        try:
            out[k] = max(0.0, min(1.0, float(v)))
        except (TypeError, ValueError):
            out[k] = 0.5
    return out


async def _react(state: State) -> State:
    group = state.get("group") or {}
    feature = state.get("feature") or {}
    response = await _llm().ainvoke(
        [
            {"role": "system", "content": SYSTEM},
            {
                "role": "user",
                "content": (
                    f"AUDIENCE GROUP:\n{json.dumps(group, ensure_ascii=False)}\n\n"
                    f"PRODUCT FEATURE:\n{json.dumps(feature, ensure_ascii=False)}\n\n"
                    "Return the JSON scores object."
                ),
            },
        ]
    )
    return {"scores": _parse_scores(response.content)}


def build_graph():
    graph = StateGraph(State)
    graph.add_node("react", _react)
    graph.add_edge(START, "react")
    graph.add_edge("react", END)
    return graph.compile()


graph = build_graph()
