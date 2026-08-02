"""
Model Router – hansı modelin nə zaman istifadə olunacağını seçir.

Ollama lokal modellər + (opsional) cloud fallback.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from dataclasses import dataclass

from core.logger import logger


@dataclass
class ModelSpec:
    name: str
    provider: str  # ollama | openai | xai
    strengths: List[str]  # reasoning, coding, creative, fast, multimodal
    context_length: int = 8192


DEFAULT_MODELS = [
    ModelSpec("llama3.2", "ollama", ["reasoning", "general", "fast"], 8192),
    ModelSpec("llama3.2:70b", "ollama", ["reasoning", "coding"], 8192),
    ModelSpec("mistral", "ollama", ["fast", "general"], 8192),
    ModelSpec("codellama", "ollama", ["coding"], 8192),
    ModelSpec("llava", "ollama", ["multimodal", "vision"], 4096),
    ModelSpec("gpt-4o-mini", "openai", ["reasoning", "coding", "fast"], 128000),
    ModelSpec("grok-3", "xai", ["reasoning", "creative"], 128000),
]


class ModelRouter:
    def __init__(self, models: Optional[List[ModelSpec]] = None):
        self.models = models or list(DEFAULT_MODELS)
        self._preferred_provider = "ollama"

    def set_provider(self, provider: str) -> None:
        self._preferred_provider = provider

    def select(
        self,
        task_type: str = "general",
        prefer_local: bool = True,
    ) -> ModelSpec:
        """
        task_type: general | reasoning | coding | creative | multimodal | fast
        """
        candidates = [
            m for m in self.models
            if task_type in m.strengths or "general" in m.strengths
        ]
        if not candidates:
            candidates = self.models

        if prefer_local:
            local = [m for m in candidates if m.provider == "ollama"]
            if local:
                chosen = local[0]
                logger.debug(f"ModelRouter → {chosen.name} (local)")
                return chosen

        # preferred provider
        preferred = [m for m in candidates if m.provider == self._preferred_provider]
        chosen = preferred[0] if preferred else candidates[0]
        logger.debug(f"ModelRouter → {chosen.name} ({chosen.provider})")
        return chosen

    def list_models(self) -> List[Dict[str, Any]]:
        return [
            {"name": m.name, "provider": m.provider, "strengths": m.strengths}
            for m in self.models
        ]
