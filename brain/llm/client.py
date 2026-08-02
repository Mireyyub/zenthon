"""
Unified LLM Client for Zenthon Brain.

OpenAI-compatible API dəstəyi:
- OpenAI
- xAI / Grok
- Any OpenAI-compatible endpoint (Ollama, vLLM, Together, Groq və s.)

Konfiqurasiya (environment variables):
    ZENTHON_LLM_API_KEY     – API açarı
    ZENTHON_LLM_BASE_URL    – Base URL (default: https://api.openai.com/v1)
    ZENTHON_LLM_MODEL       – Model adı (default: gpt-4o-mini)
    ZENTHON_LLM_TIMEOUT     – Timeout saniyə (default: 60)
"""

from __future__ import annotations

import os
import json
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

from core.logger import logger


@dataclass
class LLMConfig:
    api_key: str = ""
    base_url: str = "https://api.openai.com/v1"
    model: str = "gpt-4o-mini"
    timeout: float = 60.0
    temperature: float = 0.4
    max_tokens: int = 1024

    @classmethod
    def from_env(cls) -> "LLMConfig":
        return cls(
            api_key=os.getenv("ZENTHON_LLM_API_KEY")
            or os.getenv("OPENAI_API_KEY")
            or os.getenv("XAI_API_KEY")
            or "",
            base_url=os.getenv("ZENTHON_LLM_BASE_URL", "https://api.openai.com/v1"),
            model=os.getenv("ZENTHON_LLM_MODEL", "gpt-4o-mini"),
            timeout=float(os.getenv("ZENTHON_LLM_TIMEOUT", "60")),
            temperature=float(os.getenv("ZENTHON_LLM_TEMPERATURE", "0.4")),
            max_tokens=int(os.getenv("ZENTHON_LLM_MAX_TOKENS", "1024")),
        )


class LLMClient:
    """
    Sadə və etibarlı OpenAI-compatible chat client.
    API yoxdursa is_available=False qaytarır və heç bir sorğu göndərmir.
    """

    def __init__(self, config: Optional[LLMConfig] = None):
        self.config = config or LLMConfig.from_env()
        self._session = None

    @property
    def is_available(self) -> bool:
        return bool(self.config.api_key and self.config.api_key.strip())

    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        model: Optional[str] = None,
    ) -> Optional[str]:
        """
        Chat completion çağırışı.
        Uğurlu olarsa cavab mətnini, uğursuz olarsa None qaytarır.
        """
        if not self.is_available:
            logger.debug("LLMClient: API key yoxdur, LLM çağırışı atlanır.")
            return None

        try:
            import urllib.request
            import urllib.error

            url = self.config.base_url.rstrip("/") + "/chat/completions"
            payload = {
                "model": model or self.config.model,
                "messages": messages,
                "temperature": temperature if temperature is not None else self.config.temperature,
                "max_tokens": max_tokens or self.config.max_tokens,
            }

            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                url,
                data=data,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.config.api_key}",
                },
                method="POST",
            )

            with urllib.request.urlopen(req, timeout=self.config.timeout) as resp:
                body = json.loads(resp.read().decode("utf-8"))
                content = (
                    body.get("choices", [{}])[0]
                    .get("message", {})
                    .get("content", "")
                )
                return content.strip() if content else None

        except Exception as e:
            logger.warning(f"LLMClient error: {type(e).__name__}: {e}")
            return None

    def complete(self, prompt: str, system: Optional[str] = None, **kwargs) -> Optional[str]:
        """Sadə prompt → cavab."""
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        return self.chat(messages, **kwargs)


# Singleton-style helper
_client: Optional[LLMClient] = None


def get_llm_client(force_new: bool = False) -> LLMClient:
    global _client
    if _client is None or force_new:
        _client = LLMClient()
    return _client
