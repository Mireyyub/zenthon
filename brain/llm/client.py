"""
Unified LLM Client for Leon Brain.

Ollama (lokal), OpenAI, xAI, Groq – OpenAI-compatible.
"""

from __future__ import annotations

import os
import json
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

from core.logger import logger


PROVIDER_PRESETS = {
    "ollama": {
        "base_url": "http://localhost:11434/v1",
        "api_key": "ollama",
        "model": "llama3.2",
    },
    "openai": {
        "base_url": "https://api.openai.com/v1",
        "api_key": "",
        "model": "gpt-4o-mini",
    },
    "xai": {
        "base_url": "https://api.x.ai/v1",
        "api_key": "",
        "model": "grok-3",
    },
    "groq": {
        "base_url": "https://api.groq.com/openai/v1",
        "api_key": "",
        "model": "llama-3.3-70b-versatile",
    },
}


@dataclass
class LLMConfig:
    api_key: str = ""
    base_url: str = "http://localhost:11434/v1"
    model: str = "llama3.2"
    timeout: float = 120.0
    temperature: float = 0.4
    max_tokens: int = 1024
    provider: str = "ollama"
    embed_model: str = "nomic-embed-text"

    @classmethod
    def from_env(cls) -> "LLMConfig":
        provider = (
            os.getenv("ZENTHON_LLM_PROVIDER")
            or os.getenv("LLM_PROVIDER")
            or "ollama"
        ).lower().strip()

        preset = PROVIDER_PRESETS.get(provider, PROVIDER_PRESETS["ollama"])

        api_key = (
            os.getenv("ZENTHON_LLM_API_KEY")
            or os.getenv("OPENAI_API_KEY")
            or os.getenv("XAI_API_KEY")
            or os.getenv("GROQ_API_KEY")
            or preset.get("api_key", "")
        )

        base_url = (
            os.getenv("ZENTHON_LLM_BASE_URL")
            or preset.get("base_url", "http://localhost:11434/v1")
        )

        model = os.getenv("ZENTHON_LLM_MODEL") or preset.get("model", "llama3.2")
        embed_model = os.getenv("ZENTHON_EMBED_MODEL", "nomic-embed-text")

        if provider == "ollama" and not api_key:
            api_key = "ollama"

        return cls(
            api_key=api_key,
            base_url=base_url,
            model=model,
            timeout=float(os.getenv("ZENTHON_LLM_TIMEOUT", "120")),
            temperature=float(os.getenv("ZENTHON_LLM_TEMPERATURE", "0.4")),
            max_tokens=int(os.getenv("ZENTHON_LLM_MAX_TOKENS", "1024")),
            provider=provider,
            embed_model=embed_model,
        )


class LLMClient:
    def __init__(self, config: Optional[LLMConfig] = None):
        self.config = config or LLMConfig.from_env()

    @property
    def is_available(self) -> bool:
        if self.config.provider == "ollama":
            return True
        return bool(self.config.api_key and self.config.api_key.strip())

    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        model: Optional[str] = None,
    ) -> Optional[str]:
        if not self.is_available and self.config.provider != "ollama":
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
                "stream": False,
            }
            data = json.dumps(payload).encode("utf-8")
            headers = {"Content-Type": "application/json"}
            if self.config.api_key:
                headers["Authorization"] = f"Bearer {self.config.api_key}"

            req = urllib.request.Request(url, data=data, headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=self.config.timeout) as resp:
                body = json.loads(resp.read().decode("utf-8"))
                content = body.get("choices", [{}])[0].get("message", {}).get("content", "")
                return content.strip() if content else None

        except Exception as e:
            logger.warning(f"LLMClient chat error: {type(e).__name__}: {e}")
            return None

    def complete(self, prompt: str, system: Optional[str] = None, **kwargs) -> Optional[str]:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        return self.chat(messages, **kwargs)

    def embed(self, text: str, model: Optional[str] = None) -> Optional[List[float]]:
        """
        Embedding vektoru al.
        Ollama: /api/embeddings və ya OpenAI-compatible /v1/embeddings
        """
        try:
            import urllib.request

            emb_model = model or self.config.embed_model

            # Ollama native embeddings endpoint (daha stabil)
            if self.config.provider == "ollama":
                base = self.config.base_url.replace("/v1", "").rstrip("/")
                url = f"{base}/api/embeddings"
                payload = {"model": emb_model, "prompt": text}
            else:
                url = self.config.base_url.rstrip("/") + "/embeddings"
                payload = {"model": emb_model, "input": text}

            data = json.dumps(payload).encode("utf-8")
            headers = {"Content-Type": "application/json"}
            if self.config.api_key:
                headers["Authorization"] = f"Bearer {self.config.api_key}"

            req = urllib.request.Request(url, data=data, headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=min(60.0, self.config.timeout)) as resp:
                body = json.loads(resp.read().decode("utf-8"))

            # Ollama: {"embedding": [...]}
            if "embedding" in body and isinstance(body["embedding"], list):
                return body["embedding"]
            # OpenAI-style: {"data": [{"embedding": [...]}]}
            data_list = body.get("data") or []
            if data_list and "embedding" in data_list[0]:
                return data_list[0]["embedding"]
            return None
        except Exception as e:
            logger.debug(f"LLMClient.embed fallback: {e}")
            return None

    def list_models(self) -> List[str]:
        if self.config.provider != "ollama":
            return []
        try:
            import urllib.request

            base = self.config.base_url.replace("/v1", "").rstrip("/")
            url = f"{base}/api/tags"
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return [m.get("name", "") for m in data.get("models", [])]
        except Exception:
            return []

    def health_check(self) -> Dict[str, Any]:
        result = {
            "provider": self.config.provider,
            "base_url": self.config.base_url,
            "model": self.config.model,
            "embed_model": self.config.embed_model,
            "reachable": False,
            "models": [],
        }
        try:
            reply = self.complete("Say 'ok' in one word.", max_tokens=5)
            result["reachable"] = reply is not None
            result["test_reply"] = reply
            if self.config.provider == "ollama":
                result["models"] = self.list_models()
        except Exception as e:
            result["error"] = str(e)
        return result


_client: Optional[LLMClient] = None


def get_llm_client(force_new: bool = False) -> LLMClient:
    global _client
    if _client is None or force_new:
        _client = LLMClient()
    return _client


def use_ollama(model: str = "llama3.2", host: str = "http://localhost:11434") -> LLMClient:
    global _client
    config = LLMConfig(
        api_key="ollama",
        base_url=f"{host.rstrip('/')}/v1",
        model=model,
        provider="ollama",
        timeout=120.0,
    )
    _client = LLMClient(config)
    logger.info(f"LLM provider → Ollama | model={model} | host={host}")
    return _client
