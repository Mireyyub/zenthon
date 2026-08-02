"""Benchmark runner – agent/brain üçün test setləri."""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import time

from core.logger import logger
from evaluation.metrics import EvaluationMetrics


@dataclass
class BenchmarkCase:
    id: str
    query: str
    expected_keywords: List[str] = field(default_factory=list)
    goal: Optional[str] = None
    reasoning_mode: str = "auto"
    tags: List[str] = field(default_factory=list)


@dataclass
class CaseResult:
    case_id: str
    success: bool
    scores: Dict[str, float]
    latency_ms: float
    output_preview: str
    error: Optional[str] = None


class BenchmarkRunner:
    def __init__(self, cases: Optional[List[BenchmarkCase]] = None):
        self.cases = cases or default_cases()
        self.results: List[CaseResult] = []

    def run(
        self,
        think_fn: Callable[..., Dict[str, Any]],
        limit: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        think_fn(query, goal=..., reasoning_mode=...) -> dict with conclusion, confidence
        """
        self.results.clear()
        cases = self.cases[:limit] if limit else self.cases

        for case in cases:
            t0 = time.time()
            try:
                out = think_fn(
                    case.query,
                    goal=case.goal,
                    reasoning_mode=case.reasoning_mode,
                )
                conclusion = str(out.get("conclusion") or out.get("output") or "")
                conf = float(out.get("confidence") or 0.5)
                scores = EvaluationMetrics.composite(
                    conclusion, conf, case.expected_keywords
                )
                self.results.append(
                    CaseResult(
                        case_id=case.id,
                        success=scores["composite"] >= 0.45,
                        scores=scores,
                        latency_ms=round((time.time() - t0) * 1000, 1),
                        output_preview=conclusion[:200],
                    )
                )
            except Exception as e:
                self.results.append(
                    CaseResult(
                        case_id=case.id,
                        success=False,
                        scores={"composite": 0.0},
                        latency_ms=round((time.time() - t0) * 1000, 1),
                        output_preview="",
                        error=str(e),
                    )
                )
                logger.error(f"Benchmark case {case.id} failed: {e}")

        return self.summary()

    def summary(self) -> Dict[str, Any]:
        if not self.results:
            return {"count": 0}
        composites = [r.scores.get("composite", 0) for r in self.results]
        latencies = [r.latency_ms for r in self.results]
        passed = sum(1 for r in self.results if r.success)
        return {
            "count": len(self.results),
            "passed": passed,
            "pass_rate": round(passed / len(self.results), 3),
            "avg_composite": round(sum(composites) / len(composites), 3),
            "avg_latency_ms": round(sum(latencies) / len(latencies), 1),
            "timestamp": datetime.now().isoformat(),
            "cases": [
                {
                    "id": r.case_id,
                    "success": r.success,
                    "composite": r.scores.get("composite"),
                    "latency_ms": r.latency_ms,
                    "error": r.error,
                }
                for r in self.results
            ],
        }


def default_cases() -> List[BenchmarkCase]:
    return [
        BenchmarkCase(
            id="basic_qa",
            query="Süni intellekt nədir? Qısa izah et.",
            expected_keywords=["intellekt", "öyrən", "məlumat"],
            reasoning_mode="cot",
            tags=["qa"],
        ),
        BenchmarkCase(
            id="compare",
            query="CNN ilə Transformer fərqi nədir?",
            expected_keywords=["cnn", "transformer", "diqqət"],
            reasoning_mode="tot",
            tags=["compare"],
        ),
        BenchmarkCase(
            id="plan",
            query="Kiçik chatbot üçün 5 addımlı plan yaz.",
            expected_keywords=["plan", "addım", "model"],
            goal="İşlək plan",
            reasoning_mode="sot",
            tags=["planning"],
        ),
        BenchmarkCase(
            id="rag_concept",
            query="RAG nədir və nə üçün lazımdır?",
            expected_keywords=["retrieval", "generation", "sənəd"],
            reasoning_mode="auto",
            tags=["rag"],
        ),
        BenchmarkCase(
            id="local_llm",
            query="Ollama ilə lokal model necə işlədilir?",
            expected_keywords=["ollama", "lokal", "model"],
            reasoning_mode="cot",
            tags=["ops"],
        ),
    ]
