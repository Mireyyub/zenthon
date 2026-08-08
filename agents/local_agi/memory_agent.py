"""Memory agent — Drive Leon.təlim memory_agent, adapted."""
from __future__ import annotations
from typing import Optional
from agents.local_agi.base_agent import BaseAgent, AgentResult


class MemoryAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="memory",
            system_prompt="Sən Memory Agent-sən. Faktları yadda saxla və axtar.",
        )

    def process(self, task: str, context: Optional[dict] = None) -> AgentResult:
        context = context or {}
        bb = context.get("blackboard")
        try:
            if bb is not None and hasattr(bb, "add_fact"):
                bb.add_fact(content=task[:400], source=self.name, confidence=0.7)
                return AgentResult(
                    agent_name=self.name,
                    task_id=context.get("task_id", ""),
                    status="success",
                    output={"stored": True, "via": "blackboard"},
                    confidence=0.8,
                )
            try:
                from knowledge.facts import FactStore
                store = FactStore()
                store.add(task[:400], source=self.name)
                return AgentResult(
                    agent_name=self.name,
                    task_id=context.get("task_id", ""),
                    status="success",
                    output={"stored": True, "via": "FactStore"},
                    confidence=0.75,
                )
            except Exception:
                pass
            return AgentResult(
                agent_name=self.name,
                task_id=context.get("task_id", ""),
                status="partial",
                output={"stored": False, "reason": "no store available"},
                confidence=0.3,
            )
        except Exception as e:
            return AgentResult(
                agent_name=self.name,
                task_id=context.get("task_id", ""),
                status="failed",
                error=str(e),
            )
