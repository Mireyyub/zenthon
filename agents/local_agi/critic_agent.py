"""Critic agent — Drive Leon.təlim critic_agent, adapted."""
from __future__ import annotations
from typing import Optional
from agents.local_agi.base_agent import BaseAgent, AgentResult

try:
    from brain.llm.client import complete as llm_complete
except Exception:
    def llm_complete(prompt: str, **kwargs):
        return {"text": "", "error": "llm unavailable"}


class CriticAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="critic",
            system_prompt=(
                "Sən Critic Agent-sən. Nəticəni yoxla. "
                "JSON ver: {\"verdict\": \"pass|warn|block\", \"issues\": [], \"score\": 0.0-1.0}"
            ),
        )

    def process(self, task: str, context: Optional[dict] = None) -> AgentResult:
        context = context or {}
        try:
            resp = llm_complete(task, system=self.system_prompt)
            text = resp.get("text", "") if isinstance(resp, dict) else str(resp)
            parsed = self._parse_json_response(text)
            return AgentResult(
                agent_name=self.name,
                task_id=context.get("task_id", ""),
                status="success",
                output=parsed or {"verdict": "warn", "raw": text},
                confidence=0.7,
            )
        except Exception as e:
            return AgentResult(
                agent_name=self.name,
                task_id=context.get("task_id", ""),
                status="failed",
                error=str(e),
            )
