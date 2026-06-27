"""develop-analysis agent.

A LangGraph agent (UiPath Python Agent SDK / uipath-langchain) that turns the
aggregated audience reactions into the insights the user asked for: strengths,
weaknesses, points with potential, and/or a general report. Local Ollama, no cloud.

Only the selected insights are generated (InsightSelection flags).
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
    "You are a product analyst. Given the product's features and the aggregated "
    "audience reaction scores (0-1 per metric), produce ONLY the requested insight "
    "sections. Return ONLY valid JSON with these keys when requested: "
    '"strengths" (list of strings), "weakness" (list), "points_with_potential" (list), '
    '"final_recomendations" (list), "audience_response_analysis" (string). '
    "Omit keys that were not requested. No markdown, no fences."
)


class State(TypedDict, total=False):
    features: list
    aggregate: dict
    insights: dict
    analysis: dict


def _llm() -> ChatOpenAI:
    return ChatOpenAI(
        base_url=OLLAMA_BASE_URL,
        api_key=os.getenv("OLLAMA_API_KEY", "ollama"),
        model=OLLAMA_MODEL,
        temperature=0.3,
    )


def _requested(insights: dict) -> str:
    want = []
    if insights.get("detect_strengts"):
        want.append('"strengths"')
    if insights.get("detect_weakness"):
        want.append('"weakness"')
    if insights.get("detect_potential"):
        want.append('"points_with_potential"')
    if insights.get("general_report"):
        want.append('"audience_response_analysis" + "final_recomendations"')
    return ", ".join(want) or '"audience_response_analysis"'


def _parse(text: str) -> dict:
    text = (text or "").strip().replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(text)
    except Exception:
        i, j = text.find("{"), text.rfind("}")
        try:
            return json.loads(text[i : j + 1]) if i != -1 and j != -1 else {}
        except Exception:
            return {}


async def _analyze(state: State) -> State:
    insights = state.get("insights") or {}
    response = await _llm().ainvoke(
        [
            {"role": "system", "content": SYSTEM},
            {
                "role": "user",
                "content": (
                    f"FEATURES:\n{json.dumps(state.get('features') or [], ensure_ascii=False)}\n\n"
                    f"AGGREGATE SCORES (avg 0-1):\n{json.dumps(state.get('aggregate') or {}, ensure_ascii=False)}\n\n"
                    f"REQUESTED SECTIONS: {_requested(insights)}\n\n"
                    "Return the JSON analysis object."
                ),
            },
        ]
    )
    return {"analysis": _parse(response.content)}


def build_graph():
    graph = StateGraph(State)
    graph.add_node("analyze", _analyze)
    graph.add_edge(START, "analyze")
    graph.add_edge("analyze", END)
    return graph.compile()


graph = build_graph()
