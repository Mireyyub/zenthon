"""Reasoning agent — Drive Leon.təlim reasoning_agent, adapted."""
from __future__ import annotations
from typing import Optional
from agents.local_agi.base_agent import BaseAgent, AgentResult

try:
    from brain.llm.client import complete as llm_complete
except Exception:
    def llm_complete(prompt: str, **kwargs):
        return {"text": "", "error": "llm unavailable"}


class ReasoningAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="reasoner",
            system_prompt=(
                "Sən Reasoning Agent-sən. Problemi analiz et, hipotezlər irəli sür, "
                "riskləri qeyd et və nəticə çıxart. Azərbaycanca, lakonik."
            ),
        )

    def process(self, task: str, context: Optional[dict] = None) -> AgentResult:
        context = context or {}
        try:
            resp = llm_complete(task, system=self.system_prompt)
            text = resp.get("text", "") if isinstance(resp, dict) else str(resp)
            return AgentResult(
                agent_name=self.name,
                task_id=context.get("task_id", ""),
                status="success" if text else "failed",
                output=text,
                confidence=0.75 if text else 0.2,
            )
        except Exception as e:
            return AgentResult(
                agent_name=self.name,
                task_id=context.get("task_id", ""),
                status="failed",
                error=str(e),
            )
