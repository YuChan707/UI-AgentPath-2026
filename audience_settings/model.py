"""LLM factory for the UiPath agent.

Default: the **local Ollama** OpenAI-compatible endpoint (no cloud). When a
UiPath connection is configured (``UIPATH_BYO_CONNECTION_ID``), use the
UiPath-managed model instead — so the same agent runs locally on Ollama AND,
once published, through a UiPath connection on Orchestrator.

This module is identical across the agents (vendored, like ``contracts.py``).
"""

from __future__ import annotations

import os


def chat_model(temperature: float = 0.2):
    """Return a LangChain chat model: UiPath-managed if configured, else Ollama."""
    connection = os.getenv("UIPATH_BYO_CONNECTION_ID", "").strip()
    if connection:
        # UiPath-managed model (routes through a registered UiPath connection).
        from uipath_langchain.chat import UiPathChatOpenAI

        return UiPathChatOpenAI(
            byo_connection_id=connection,
            model_name=os.getenv("UIPATH_MODEL_NAME", os.getenv("OLLAMA_MODEL", "llama3.1")),
        )

    # Local Ollama (OpenAI-compatible) — the default, fully local.
    from langchain_openai import ChatOpenAI

    return ChatOpenAI(
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1"),
        api_key=os.getenv("OLLAMA_API_KEY", "ollama"),
        model=os.getenv("OLLAMA_MODEL", "llama3.1"),
        temperature=temperature,
    )


__all__ = ["chat_model"]
