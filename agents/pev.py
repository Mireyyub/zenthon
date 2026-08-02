"""
Plan-Execute-Verify (PEV) – plan qur, icra et, yoxla.

İlham: plan-and-execute + verification loops (agentic architectures).
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from agents.base import BaseAgent, AgentResult
from core.logger import logger


class PEVAgent(BaseAgent):
    def __init__(self, name: str = "PEVAgent", description: str = "Plan-Execute-Verify agent"):
        super().__init__(name=name, description=description)

    def run(self, task: str, context: Optional[Dict[str, Any]] = None) -> AgentResult:
        context = context or {}
        try:
            from brain import ThinkingBrain

            brain = ThinkingBrain(name="PEVBrain", enable_meta=True)

            # 1. Plan
            plan_result = brain.think(
                f"Bu tapşırıq üçün addım-addım plan yaz: {task}",
                goal="İcra oluna bilən plan",
                reasoning_mode="sot",
            )
            plan_text = plan_result.get("conclusion") or ""
            plan_steps = plan_result.get("trace") or [plan_text]

            # 2. Execute (simulate step execution via short thinks)
            executions = []
            for i, step in enumerate(plan_steps[:5], 1):
                step_r = brain.think(
                    f"Plan addımını icra et / nəticələndir: {step}",
                    goal=task,
                    reasoning_mode="cot",
                    allow_rethink=False,
                )
                executions.append({
                    "step": i,
                    "description": str(step)[:120],
                    "result": step_r.get("conclusion"),
                    "confidence": step_r.get("confidence"),
                })

            # 3. Verify
            verify = brain.think(
                f"Tapşırıq: {task}\n\nİcra nəticələri: {executions}\n\n"
                f"Məqsədə çatdımı? Çatışmazlıqları və yekun qiyməti yaz.",
                goal="Dürüst verifikasiya",
                reasoning_mode="tot",
            )

            return AgentResult(
                success=True,
                output={
                    "plan": plan_text,
                    "executions": executions,
                    "verification": verify.get("conclusion"),
                    "verify_confidence": verify.get("confidence"),
                },
                metadata={
                    "method": "plan_execute_verify",
                    "plan_confidence": plan_result.get("confidence"),
                    "reflection": verify.get("reflection"),
                },
            )
        except Exception as e:
            logger.error(f"PEV failed: {e}")
            return AgentResult(success=False, error=str(e))
