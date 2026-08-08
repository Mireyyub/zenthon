"""Planner agent — Drive Leon.təlim planner_agent, adapted."""
from __future__ import annotations
from typing import Optional
from agents.local_agi.base_agent import BaseAgent, AgentResult
from core.logger import logger

try:
    from brain.llm.client import complete as llm_complete
except Exception:
    def llm_complete(prompt: str, **kwargs):
        return {"text": "", "error": "llm unavailable"}


class PlannerAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="planner",
            system_prompt=(
                "Sən Planner Agent-sən. Tapşırığı alt-tapşırıqlara böl. "
                "JSON çıxış ver: {\"sub_tasks\": [{\"id\": \"t1\", \"description\": \"...\", \"agent\": \"executor|reasoner|memory\"}]}"
            ),
        )

    def process(self, task: str, context: Optional[dict] = None) -> AgentResult:
        context = context or {}
        prompt = f"Tapşırığı alt-tapşırıqlara böl:\n{task}\n\nYalnız JSON cavab ver."
        try:
            resp = llm_complete(prompt, system=self.system_prompt)
            text = resp.get("text", "") if isinstance(resp, dict) else str(resp)
            parsed = self._parse_json_response(text)
            return AgentResult(
                agent_name=self.name,
                task_id=context.get("task_id", ""),
                status="success" if parsed else "partial",
                output=parsed or text,
                confidence=0.8 if parsed else 0.4,
            )
        except Exception as e:
            logger.error(f"[planner] {e}")
            return AgentResult(
                agent_name=self.name,
                task_id=context.get("task_id", ""),
                status="failed",
                error=str(e),
            )
