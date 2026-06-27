"""features-extractor agent.

A LangGraph graph (UiPath Python Agent SDK / uipath-langchain compatible) that
extracts a product's FEATURES from its document chunks, using a **local Ollama**
model (no cloud). The compiled ``graph`` is what UiPath packs (see
``langgraph.json``) and what the Dapr handler invokes.

Prompt origin: agent_prompts/document_analysis.md (salvaged from the old monolith).
"""

from __future__ import annotations

import json
import os
from typing import TypedDict

from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1")

SYSTEM = (
    "You are a product analyst. From the document excerpts, extract the product's "
    "main FEATURES — the concrete capabilities/fields a user cares about and will "
    "react to. Return ONLY valid JSON: a list of objects "
    '{"feature_id": "<short_slug>", "name": "<short name>", '
    '"description": "<one sentence, raw>"}. No markdown, no prose, no fences.'
)


class State(TypedDict, total=False):
    collection: str
    chunks: list[str]
    features: list[dict]


def _llm() -> ChatOpenAI:
    # Direct connection to the local Ollama OpenAI-compatible endpoint.
    return ChatOpenAI(
        base_url=OLLAMA_BASE_URL,
        api_key=os.getenv("OLLAMA_API_KEY", "ollama"),
        model=OLLAMA_MODEL,
        temperature=0.2,
    )


def _parse_features(text: str) -> list[dict]:
    """Recover the JSON list of features from the model output (tolerant)."""
    text = (text or "").strip().replace("```json", "").replace("```", "").strip()
    try:
        data = json.loads(text)
    except Exception:
        i, j = text.find("["), text.rfind("]")
        data = json.loads(text[i : j + 1]) if i != -1 and j != -1 else []
    return [f for f in data if isinstance(f, dict)] if isinstance(data, list) else []


async def _extract(state: State) -> State:
    chunks = state.get("chunks") or []
    document = "\n\n".join(chunks[:40])
    response = await _llm().ainvoke(
        [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": f"Document excerpts:\n{document}\n\nReturn the JSON list of features."},
        ]
    )
    return {"features": _parse_features(response.content)}


def build_graph():
    graph = StateGraph(State)
    graph.add_node("extract", _extract)
    graph.add_edge(START, "extract")
    graph.add_edge("extract", END)
    return graph.compile()


# Exported compiled graph (referenced by langgraph.json and the Dapr handler).
graph = build_graph()
