"""
Reflection System – sistemin öz fəaliyyətini analiz etməsi.

- Səhv analizi
- Performans qiymətləndirməsi
- Strategiya dəyişməsi tövsiyələri
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass, field

from core.logger import logger


@dataclass
class ReflectionReport:
    cycle: int
    quality: str  # good | acceptable | poor
    issues: List[str] = field(default_factory=list)
    strengths: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    confidence_adjustment: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class ReflectionEngine:
    """Meta-cognitive reflection over reasoning results."""

    LOW = 0.55
    HIGH = 0.82

    def reflect(
        self,
        reasoning_result: Dict[str, Any],
        context_size: int = 0,
        cycle: int = 0,
        goal: Optional[str] = None,
    ) -> ReflectionReport:
        conf = float(reasoning_result.get("confidence", 0.5))
        method = reasoning_result.get("method", "unknown")
        trace = reasoning_result.get("trace", [])
        llm_used = reasoning_result.get("llm_used", False)

        issues: List[str] = []
        strengths: List[str] = []
        suggestions: List[str] = []
        adj = 0.0

        # Trace analysis
        if len(trace) < 3:
            issues.append("düşüncə izi çox qısadır")
            adj -= 0.05
        else:
            strengths.append(f"kifayət qədər addım ({len(trace)})")

        # Confidence bands
        if conf < self.LOW:
            issues.append("aşağı etimad")
            suggestions.append("Fərqli reasoning mode (tot/sot) ilə yenidən düşün")
            adj -= 0.04
        elif conf >= self.HIGH:
            strengths.append("yüksək etimad")
            adj += 0.02

        # Context
        if context_size == 0:
            issues.append("kontekst / yaddaş istifadə olunmayıb")
            suggestions.append("Uyğun faktları MemoryManager və ya Knowledge-dən yüklə")
            adj -= 0.03
        else:
            strengths.append(f"kontekst var ({context_size} element)")

        # Goal alignment
        if goal:
            strengths.append("məqsəd təyin edilib")
            adj += 0.02
        else:
            suggestions.append("Daha dəqiq nəticə üçün goal təyin et")

        # LLM vs fallback
        if llm_used:
            strengths.append("real LLM istifadə olunub")
            adj += 0.03
        else:
            suggestions.append("Ollama/LLM aktiv etsən keyfiyyət yüksələr")

        # Quality label
        if not issues:
            quality = "good"
        elif len(issues) <= 2 and conf >= self.LOW:
            quality = "acceptable"
        else:
            quality = "poor"

        report = ReflectionReport(
            cycle=cycle,
            quality=quality,
            issues=issues,
            strengths=strengths,
            suggestions=suggestions,
            confidence_adjustment=round(adj, 3),
        )
        logger.debug(
            f"Reflection cycle={cycle} quality={quality} adj={adj:+.3f}"
        )
        return report

    def apply(self, reasoning_result: Dict[str, Any], report: ReflectionReport) -> Dict[str, Any]:
        """Confidence-i reflection-a görə tənzimlə və hesabatı əlavə et."""
        conf = float(reasoning_result.get("confidence", 0.5))
        conf = max(0.2, min(0.97, conf + report.confidence_adjustment))
        out = dict(reasoning_result)
        out["confidence"] = round(conf, 3)
        out["reflection"] = {
            "quality": report.quality,
            "issues": report.issues,
            "strengths": report.strengths,
            "suggestions": report.suggestions,
        }
        return out
