"""
brain/llm/async_client.py — Optional async Ollama / OpenAI-compatible client.
Source: Drive zenthon_v09 async_client ideas, heavily simplified for zenthon.

- Soft dependency on httpx (already in requirements)
- Falls back gracefully if async not needed
- Uses existing brain.llm.cache when available
"""
from __future__ import annotations

import asyncio
import os
import time
from dataclasses import dataclass
from typing import Any, Optional

from core.logger import logger

try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False
    httpx = None  # type: ignore


@dataclass
class AsyncCompletionResult:
    text: str
    model: str
    latency_ms: float
    cached: bool = False
    error: Optional[str] = None


class AsyncLLMClient:
    """
    Minimal async client for local Ollama (or any OpenAI-compatible /api/chat).
    Prefer the sync brain.llm.client for most paths; use this only when
    concurrent requests are genuinely needed (swarm, batch).
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: float = 60.0,
        max_concurrent: int = 8,
    ):
        self.base_url = (base_url or os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")).rstrip("/")
        self.model = model or os.getenv("LEON_LLM_MODEL", "llama3.2")
        self.timeout = timeout
        self._sem = asyncio.Semaphore(max_concurrent)
        self._client: Any = None

    async def _get_client(self):
        if not HAS_HTTPX:
            raise RuntimeError("httpx not installed")
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self._client

    async def complete(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.4,
        max_tokens: int = 1024,
    ) -> AsyncCompletionResult:
        t0 = time.time()
        if not HAS_HTTPX:
            return AsyncCompletionResult(
                text="", model=self.model, latency_ms=0.0,
                error="httpx missing — use sync client",
            )

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": temperature, "num_predict": max_tokens},
        }

        try:
            async with self._sem:
                client = await self._get_client()
                url = f"{self.base_url}/api/chat"
                resp = await client.post(url, json=payload)
                resp.raise_for_status()
                data = resp.json()
                text = data.get("message", {}).get("content", "") or data.get("response", "")
                latency = (time.time() - t0) * 1000
                return AsyncCompletionResult(
                    text=text.strip(), model=self.model, latency_ms=latency
                )
        except Exception as e:
            logger.warning(f"[AsyncLLMClient] complete failed: {e}")
            return AsyncCompletionResult(
                text="", model=self.model,
                latency_ms=(time.time() - t0) * 1000,
                error=str(e),
            )

    async def close(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None


_async_client: Optional[AsyncLLMClient] = None


def get_async_client() -> AsyncLLMClient:
    global _async_client
    if _async_client is None:
        _async_client = AsyncLLMClient()
    return _async_client
