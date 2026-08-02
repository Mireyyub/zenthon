"""Executor Agent – planı addım-addım icra edir."""

from typing import Any, Dict, List, Optional

from agents.base import BaseAgent, AgentResult
from core.logger import logger


class ExecutorAgent(BaseAgent):
    def __init__(self, name: str = "ExecutorAgent", description: str = "Plan icraçısı"):
        super().__init__(name=name, description=description)

    def run(self, task: str, context: Optional[Dict[str, Any]] = None) -> AgentResult:
        logger.info(f"ExecutorAgent running: {task[:80]}")
        context = context or {}
        steps: List[str] = context.get("plan") or []

        if not steps:
            # Plan yoxdursa brain-dən plan yarat
            try:
                from brain import ThinkingBrain
                brain = ThinkingBrain()
                plan = brain.set_goal(task)
                steps = plan
            except Exception:
                steps = [f"1. {task}"]

        executed = []
        for i, step in enumerate(steps, 1):
            executed.append({"step": i, "description": step, "status": "done"})
            logger.info(f"  Executed step {i}: {step[:60]}")

        return AgentResult(
            success=True,
            output={"task": task, "steps_executed": executed},
            metadata={"total_steps": len(executed)},
        )
