"""
Unified LLM Client for Leon Brain.

Ollama (lokal), OpenAI, xAI, Groq – OpenAI-compatible.
Konfiq: core.config.LLMSettings (env: LEON_* / ZENTHON_*).
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

from core.logger import logger


@dataclass
class LLMConfig:
    api_key: str = "ollama"
    base_url: str = "http://localhost:11434/v1"
    model: str = "llama3.2"
    timeout: float = 120.0
    temperature: float = 0.4
    max_tokens: int = 1024
    provider: str = "ollama"
    embed_model: str = "nomic-embed-text"

    @classmethod
    def from_env(cls) -> "LLMConfig":
        try:
            from core.config import config

            s = config.llm
            return cls(
                api_key=s.api_key or "ollama",
                base_url=s.base_url,
                model=s.model,
                timeout=s.timeout,
                temperature=s.temperature,
                max_tokens=s.max_tokens,
                provider=s.provider,
                embed_model=s.embed_model,
            )
        except Exception:
            # extreme fallback
            return cls()


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
        try:
            import urllib.request

            emb_model = model or self.config.embed_model

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

            if "embedding" in body and isinstance(body["embedding"], list):
                return body["embedding"]
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
    cfg = LLMConfig(
        api_key="ollama",
        base_url=f"{host.rstrip('/')}/v1",
        model=model,
        provider="ollama",
        timeout=120.0,
    )
    _client = LLMClient(cfg)
    logger.info(f"LLM provider → Ollama | model={model} | host={host}")
    return _client
