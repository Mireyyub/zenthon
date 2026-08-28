"""LLM integration package for Zenthon Brain."""

from brain.llm.client import LLMClient, get_llm_client, use_ollama, LLMConfig
from brain.llm.ollama_manager import ensure_ollama
from brain.llm.provider import (
    LLMProvider,
    LLMMessage,
    LLMCompletion,
    LLMHealth,
    OllamaProvider,
    MockProvider,
    get_llm_provider,
    set_llm_provider,
)

__all__ = [
    "LLMClient",
    "get_llm_client",
    "use_ollama",
    "LLMConfig",
    "ensure_ollama",
    "LLMProvider",
    "LLMMessage",
    "LLMCompletion",
    "LLMHealth",
    "OllamaProvider",
    "MockProvider",
    "get_llm_provider",
    "set_llm_provider",
]
