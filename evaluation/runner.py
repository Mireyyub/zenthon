"""High-level evaluation entrypoints."""

from __future__ import annotations

from typing import Any, Dict, Optional

from core.logger import logger
from evaluation.benchmark import BenchmarkRunner, default_cases


def evaluate_brain(limit: Optional[int] = None) -> Dict[str, Any]:
    """ThinkingBrain üzərində default benchmark işə sal."""
    from brain import ThinkingBrain

    brain = ThinkingBrain(name="EvalBrain", enable_meta=True)

    def think_fn(query, goal=None, reasoning_mode="auto"):
        return brain.think(query, goal=goal, reasoning_mode=reasoning_mode)

    runner = BenchmarkRunner(default_cases())
    summary = runner.run(think_fn, limit=limit)
    logger.info(
        f"Brain eval: pass_rate={summary.get('pass_rate')} "
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
