"""LLM integration package for Zenthon Brain."""

from brain.llm.client import LLMClient, get_llm_client, use_ollama, LLMConfig
from brain.llm.ollama_manager import ensure_ollama

__all__ = ["LLMClient", "get_llm_client", "use_ollama", "LLMConfig", "ensure_ollama"]
