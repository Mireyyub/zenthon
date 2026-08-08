"""Evaluation – curriculum + ReasoningEngine path (not legacy ThinkingBrain)."""

from __future__ import annotations

from typing import Any, Dict, Optional

from core.logger import logger
from evaluation.benchmark import BenchmarkRunner, default_cases


def evaluate_brain(limit: Optional[int] = None) -> Dict[str, Any]:
    """Evaluate via ReasoningEngine (canonical)."""
    from brain.reasoning.engine import ReasoningEngine

    eng = ReasoningEngine(persist_traces=False)

    def think_fn(query, goal=None, reasoning_mode="auto"):
        r = eng.reason(query, strategy=reasoning_mode or "auto", goal=goal, use_brain=True)
        return {
            "conclusion": r.get("answer"),
            "confidence": r.get("confidence"),
            "reasoning_mode": r.get("reasoning_mode"),
            "source": r.get("source"),
        }

    runner = BenchmarkRunner(default_cases())
    summary = runner.run(think_fn, limit=limit)
    logger.info(
        f"ReasoningEngine eval: pass_rate={summary.get('pass_rate')} "
        f"avg={summary.get('avg_composite')} latency={summary.get('avg_latency_ms')}ms"
    )
    return summary


def evaluate_orchestrator(limit: Optional[int] = None) -> Dict[str, Any]:
    from brain.orchestrator import BrainOrchestrator

    orch = BrainOrchestrator()

    def think_fn(query, goal=None, reasoning_mode="auto"):
        return orch.run(query, goal=goal, reasoning_mode=reasoning_mode, use_session=False)

    runner = BenchmarkRunner(default_cases())
    return runner.run(think_fn, limit=limit)


def evaluate_curriculum(volume_id: str = "01", teach_first: bool = True) -> Dict[str, Any]:
    from curriculum import CurriculumEngine

    eng = CurriculumEngine()
    if teach_first:
        try:
            eng.teach_volume(volume_id)
        except Exception as e:
            logger.warning(f"teach_volume before eval: {e}")
    report = eng.run_eval(volume_id)
    logger.info(
        f"Curriculum eval vol={volume_id}: "
        f"{report.get('passed')}/{report.get('total')} "
        f"pass_rate={report.get('pass_rate')}"
    )
    return report
