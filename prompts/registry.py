"""
Leon Prompt Registry — v1.0
Source: Drive zenthon_v10 prompts/registry.py, adapted for zenthon.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime

from core.logger import logger


@dataclass
class PromptTemplate:
    name: str
    version: str
    template: str
    description: str = ""
    variables: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    calls: int = 0
    success_rate: float = 0.0
    avg_latency_ms: float = 0.0

    def render(self, **kwargs: Any) -> str:
        result = self.template
        for key, value in kwargs.items():
            result = result.replace("{{"+key+"}}", str(value))
        unreplaced = re.findall(r"\{\{(\w+)\}\}", result)
        if unreplaced:
            logger.warning(f"Prompt '{self.name}' has unreplaced variables: {unreplaced}")
        return result

    def record_call(self, success: bool, latency_ms: float) -> None:
        self.calls += 1
        self.success_rate = 0.3 * (1.0 if success else 0.0) + 0.7 * self.success_rate
        self.avg_latency_ms = 0.3 * latency_ms + 0.7 * self.avg_latency_ms

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "template": self.template,
            "description": self.description,
            "variables": self.variables,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "metrics": {
                "calls": self.calls,
                "success_rate": round(self.success_rate, 4),
                "avg_latency_ms": round(self.avg_latency_ms, 2),
            },
        }


class PromptRegistry:
    def __init__(self, prompts_dir: Optional[Path] = None):
        if prompts_dir is None:
            try:
                from core.config import config
                prompts_dir = Path(config.path.memory_dir).parent / "prompts"
            except Exception:
                prompts_dir = Path("data/leon/prompts")
        self.prompts_dir = Path(prompts_dir)
        self.prompts_dir.mkdir(parents=True, exist_ok=True)
        self._templates: Dict[str, PromptTemplate] = {}
        self._load_builtin_templates()
        self._load_from_disk()

    def _load_builtin_templates(self) -> None:
        builtins = [
            PromptTemplate(
                name="system_default",
                version="1.0",
                template=(
                    "Sən Leon adlı kognitiv AI-assistantsan. "
                    "Düşünərək, yadda saxlayaraq və səbəb-nəticə əlaqələri quraraq cavab verirsən. "
                    "Cavabların qısa, dəqiq və faydalı olsun."
                ),
                description="Default system prompt",
            ),
            PromptTemplate(
                name="system_expert",
                version="1.0",
                template=(
                    "Sən {{domain}} sahəsində ekspert AI-assistantsan. "
                    "Texniki detallara diqqət yetir, mənbələrə istinad et, "
                    "və mümkünsə kod nümunələri ilə izah et."
                ),
                description="Expert mode system prompt",
                variables=["domain"],
            ),
            PromptTemplate(
                name="rag_answer",
                version="1.0",
                template=(
                    "Aşağıdakı kontekstə əsaslanaraq suala cavab ver. "
                    "Əgər cavab kontekstdə yoxdursa, 'Bilmirəm' de. "
                    "Cavabı qısa və dəqiq yaz.\n\n"
                    "Kontekst:\n{{context}}\n\n"
                    "Sual: {{question}}\n\nCavab:"
                ),
                description="RAG answer generation",
                variables=["context", "question"],
            ),
            PromptTemplate(
                name="summarize",
                version="1.0",
                template="Aşağıdakı mətni 2-3 cümlə ilə xülasə et:\n\n{{text}}\n\nXülasə:",
                description="Text summarization",
                variables=["text"],
            ),
            PromptTemplate(
                name="code_review",
                version="1.0",
                template=(
                    "Aşağıdakı kodu nəzərdən keçir. Xətalar, təhlükəsizlik problemləri, "
                    "və optimallaşdırma imkanlarını göstər:\n\n```{{language}}\n{{code}}\n```\n\nTəhlil:"
                ),
                description="Code review prompt",
                variables=["language", "code"],
            ),
            PromptTemplate(
                name="translate",
                version="1.0",
                template="Aşağıdakı mətni {{target_language}} dilinə tərcümə et:\n\n{{text}}\n\nTərcümə:",
                description="Translation prompt",
                variables=["target_language", "text"],
            ),
            PromptTemplate(
                name="tool_use",
                version="1.0",
                template=(
                    "Sual: {{question}}\n"
                    "Mövcud alətlər:\n{{tools}}\n"
                    "Əgər alət lazımdırsa, JSON formatında çağırış et. "
                    "Format: {\"tool\": \"name\", \"arguments\": {}}"
                ),
                description="Tool calling prompt",
                variables=["question", "tools"],
            ),
        ]
        for t in builtins:
            self.register(t)

    def register(self, template: PromptTemplate) -> None:
        key = f"{template.name}@{template.version}"
        self._templates[key] = template
        logger.info(f"Prompt template registered: {key}")

    def get(self, name: str, version: Optional[str] = None) -> Optional[PromptTemplate]:
        if version:
            return self._templates.get(f"{name}@{version}")
        matches = [k for k in self._templates if k.startswith(name + "@")]
        if not matches:
            return None
        matches.sort(key=lambda k: k.split("@")[1])
        return self._templates[matches[-1]]

    def render(self, name: str, version: Optional[str] = None, **kwargs: Any) -> Optional[str]:
        template = self.get(name, version)
        if not template:
            logger.error(f"Prompt template not found: {name}@{version or 'latest'}")
            return None
        return template.render(**kwargs)

    def list_templates(self) -> List[Dict[str, Any]]:
        return [t.to_dict() for t in self._templates.values()]

    def save_template(self, template: PromptTemplate) -> None:
        path = self.prompts_dir / f"{template.name}_{template.version}.json"
        path.write_text(json.dumps(template.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")

    def _load_from_disk(self) -> None:
        if not self.prompts_dir.exists():
            return
        for path in self.prompts_dir.glob("*.json"):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                template = PromptTemplate(
                    name=data["name"],
                    version=data["version"],
                    template=data["template"],
                    description=data.get("description", ""),
                    variables=data.get("variables", []),
                    metadata=data.get("metadata", {}),
                )
                metrics = data.get("metrics", {})
                template.calls = metrics.get("calls", 0)
                template.success_rate = metrics.get("success_rate", 0.0)
                template.avg_latency_ms = metrics.get("avg_latency_ms", 0.0)
                self.register(template)
            except Exception as e:
                logger.warning(f"Failed to load prompt template from {path}: {e}")

    def get_best_version(self, name: str) -> Optional[PromptTemplate]:
        matches = [t for k, t in self._templates.items() if k.startswith(name + "@")]
        if not matches:
            return None
        return max(matches, key=lambda t: t.success_rate)


_registry_instance: Optional[PromptRegistry] = None


def get_prompt_registry() -> PromptRegistry:
    global _registry_instance
    if _registry_instance is None:
        _registry_instance = PromptRegistry()
    return _registry_instance


def render_prompt(name: str, version: Optional[str] = None, **kwargs: Any) -> Optional[str]:
    return get_prompt_registry().render(name, version, **kwargs)


# Alias expected by prompts/__init__.py
prompt_registry = get_prompt_registry()
