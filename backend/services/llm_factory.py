"""
Returns an async OpenAI-compatible chat client.

Default backend is a local Ollama server running llama3.1 (fully local, no cloud).
Set LLM_BACKEND=groq to use Groq's OpenAI-compatible endpoint instead.

Both expose the same AsyncOpenAI interface so callers don't change.
"""
import os
from openai import AsyncOpenAI

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1")


def _use_groq() -> bool:
    return os.getenv("LLM_BACKEND", "ollama").strip().lower() == "groq"


def get_llm_client() -> AsyncOpenAI:
    if _use_groq():
        return AsyncOpenAI(
            base_url="https://api.groq.com/openai/v1",
            api_key=os.getenv("GROQ_API_KEY", ""),
        )
    # Default: local Ollama (OpenAI-compatible; no real API key required)
    return AsyncOpenAI(
        base_url=OLLAMA_BASE_URL,
        api_key=os.getenv("OLLAMA_API_KEY", "ollama"),
    )


def get_model(fast: bool = True) -> str:
    """Return the model name for the active backend."""
    if _use_groq():
        return "llama-3.1-8b-instant" if fast else "llama-3.3-70b-versatile"
    return OLLAMA_MODEL
