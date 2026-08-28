"""
LLMProvider abstraction (Phase 1 contract).

Existing brain.llm.client.LLMClient remains the working implementation.
This module defines the stable interface and adapters so future phases
can swap Ollama / Mock / remote providers without touching ReasoningEngine.

Rule: no silent network failure presented as success.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from core.logger import logger


@dataclass
class LLMMessage:
    role: str  # system | user | assistant
    content: str


@dataclass
class LLMCompletion:
    text: str
    model: str
    provider: str
    latency_ms: float = 0.0
    cached: bool = False
    error: Optional[str] = None
    raw: Optional[Dict[str, Any]] = None

    @property
    def ok(self) -> bool:
        return self.error is None and bool(self.text)


@dataclass
class LLMHealth:
    provider: str
    reachable: bool
    model: str = ""
    models: List[str] = field(default_factory=list)
    offline: bool = True
    error: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "provider": self.provider,
            "reachable": self.reachable,
            "model": self.model,
            "models": list(self.models),
            "offline": self.offline,
            "error": self.error,
            "details": self.details,
        }


class LLMProvider(ABC):
    """Stable LLM surface for cognitive core."""

    name: str = "base"

    @abstractmethod
    def complete(
        self,
        prompt: str,
        *,
        system: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        model: Optional[str] = None,
    ) -> LLMCompletion:
        ...

    @abstractmethod
    def chat(
        self,
        messages: List[LLMMessage] | List[Dict[str, str]],
        *,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        model: Optional[str] = None,
    ) -> LLMCompletion:
        ...

    def embed(self, text: str, model: Optional[str] = None) -> Optional[List[float]]:
        """Optional; return None if provider has no embeddings."""
        return None

    def list_models(self) -> List[str]:
        return []

    @abstractmethod
    def health(self) -> LLMHealth:
        ...

    @property
    def is_available(self) -> bool:
        try:
            return self.health().reachable
        except Exception:
            return False


def _normalize_messages(
    messages: List[LLMMessage] | List[Dict[str, str]],
) -> List[Dict[str, str]]:
    out: List[Dict[str, str]] = []
    for m in messages:
        if isinstance(m, LLMMessage):
            out.append({"role": m.role, "content": m.content})
        elif isinstance(m, dict):
            out.append({"role": str(m.get("role", "user")), "content": str(m.get("content", ""))})
    return out


class OllamaProvider(LLMProvider):
    """Adapter over existing LLMClient — zero behavior change."""

    name = "ollama"

    def __init__(self, client: Any = None):
        if client is None:
            from brain.llm.client import get_llm_client

            client = get_llm_client()
        self._client = client

    def complete(
        self,
        prompt: str,
        *,
        system: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        model: Optional[str] = None,
    ) -> LLMCompletion:
        import time

        t0 = time.time()
        try:
            text = self._client.complete(
                prompt,
                system=system,
                temperature=temperature,
                max_tokens=max_tokens,
                model=model,
            )
            latency = (time.time() - t0) * 1000
            if text is None:
                return LLMCompletion(
                    text="",
                    model=model or getattr(self._client.config, "model", ""),
                    provider=self.name,
                    latency_ms=latency,
                    error="no_response",
                )
            return LLMCompletion(
                text=text,
                model=model or getattr(self._client.config, "model", ""),
                provider=self.name,
                latency_ms=latency,
            )
        except Exception as e:
            logger.warning(f"OllamaProvider.complete: {type(e).__name__}: {e}")
            return LLMCompletion(
                text="",
                model=model or "",
                provider=self.name,
                latency_ms=(time.time() - t0) * 1000,
                error=str(e),
            )

    def chat(
        self,
        messages: List[LLMMessage] | List[Dict[str, str]],
        *,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        model: Optional[str] = None,
    ) -> LLMCompletion:
        import time

        t0 = time.time()
        msgs = _normalize_messages(messages)
        try:
            text = self._client.chat(
                msgs,
                temperature=temperature,
                max_tokens=max_tokens,
                model=model,
            )
            latency = (time.time() - t0) * 1000
            if text is None:
                return LLMCompletion(
                    text="",
                    model=model or getattr(self._client.config, "model", ""),
                    provider=self.name,
                    latency_ms=latency,
                    error="no_response",
                )
            return LLMCompletion(
                text=text,
                model=model or getattr(self._client.config, "model", ""),
                provider=self.name,
                latency_ms=latency,
            )
        except Exception as e:
            logger.warning(f"OllamaProvider.chat: {type(e).__name__}: {e}")
            return LLMCompletion(
                text="",
                model=model or "",
                provider=self.name,
                latency_ms=(time.time() - t0) * 1000,
                error=str(e),
            )

    def embed(self, text: str, model: Optional[str] = None) -> Optional[List[float]]:
        try:
            return self._client.embed(text, model=model)
        except Exception:
            return None

    def list_models(self) -> List[str]:
        try:
            return list(self._client.list_models() or [])
        except Exception:
            return []

    def health(self) -> LLMHealth:
        try:
            raw = self._client.health_check()
            reachable = bool(raw.get("reachable"))
            return LLMHealth(
                provider=self.name,
                reachable=reachable,
                model=str(raw.get("model") or ""),
                models=list(raw.get("models") or []),
                offline=not reachable,
                error=raw.get("error"),
                details=dict(raw),
            )
        except Exception as e:
            return LLMHealth(
                provider=self.name,
                reachable=False,
                offline=True,
                error=str(e),
            )


class MockProvider(LLMProvider):
    """Deterministic offline provider for tests and no-LLM environments."""

    name = "mock"

    def __init__(self, fixed_reply: str = "[mock] OK"):
        self.fixed_reply = fixed_reply

    def complete(
        self,
        prompt: str,
        *,
        system: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        model: Optional[str] = None,
    ) -> LLMCompletion:
        return LLMCompletion(
            text=self.fixed_reply,
            model=model or "mock",
            provider=self.name,
            latency_ms=0.0,
        )

    def chat(
        self,
        messages: List[LLMMessage] | List[Dict[str, str]],
        *,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        model: Optional[str] = None,
    ) -> LLMCompletion:
        return LLMCompletion(
            text=self.fixed_reply,
            model=model or "mock",
            provider=self.name,
            latency_ms=0.0,
        )

    def health(self) -> LLMHealth:
        return LLMHealth(
            provider=self.name,
            reachable=True,
            model="mock",
            models=["mock"],
            offline=True,  # no network by design
        )


_provider: Optional[LLMProvider] = None


def get_llm_provider(
    force_new: bool = False,
    prefer: Optional[str] = None,
) -> LLMProvider:
    """
    Factory. Default: OllamaProvider wrapping existing LLMClient.
    prefer="mock" forces MockProvider (tests / offline CI).
    """
    global _provider
    if prefer == "mock":
        return MockProvider()
    if _provider is None or force_new:
        try:
            _provider = OllamaProvider()
        except Exception as e:
            logger.warning(f"get_llm_provider: falling back to Mock: {e}")
            _provider = MockProvider()
    return _provider


def set_llm_provider(provider: LLMProvider) -> None:
    global _provider
    _provider = provider
