"""Execution agent — Drive Leon.təlim execution_agent, adapted."""
from __future__ import annotations
from typing import Optional
from agents.local_agi.base_agent import BaseAgent, AgentResult
from core.logger import logger

try:
    from tools.registry import get_registry
except Exception:
    get_registry = None


class ExecutionAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="executor",
            system_prompt="Sən Execution Agent-sən. Alətlərlə tapşırığı icra et.",
        )

    def process(self, task: str, context: Optional[dict] = None) -> AgentResult:
        context = context or {}
        try:
            if get_registry:
                reg = get_registry()
                if any(k in task.lower() for k in ("hesabla", "calculate", "math")):
                    tool = reg.get("calc") if hasattr(reg, "get") else None
                    if tool:
                        out = tool(task)
                        return AgentResult(
                            agent_name=self.name,
                            task_id=context.get("task_id", ""),
                            status="success",
                            output=out,
                            confidence=0.85,
                        )
            return AgentResult(
                agent_name=self.name,
                task_id=context.get("task_id", ""),
                status="partial",
                output={"note": "no matching tool; task logged", "task": task[:200]},
                confidence=0.4,
            )
        except Exception as e:
            logger.error(f"[executor] {e}")
            return AgentResult(
                agent_name=self.name,
                task_id=context.get("task_id", ""),
                status="failed",
                error=str(e),
            )
