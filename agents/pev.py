"""PEV Agent – EXPERIMENTAL Plan-Execute-Verify skeleton."""

from __future__ import annotations

from typing import Any, Dict, Optional

from agents.base import BaseAgent, AgentResult


class PEVAgent(BaseAgent):
    PRODUCTION = False

    def __init__(self, name: str = "PEVAgent", description: str = "Experimental PEV"):
        super().__init__(name=name, description=description)

    def run(self, task: str, context: Optional[Dict[str, Any]] = None) -> AgentResult:
        # Minimal honest loop: plan text → try react once → report
        plan = [f"1. Anla: {task[:80]}", "2. Evidence topla", "3. Cavab ver / verify"]
        try:
            from agents.manager import agent_manager

            react = agent_manager.create("react", allow_experimental=False)
            res = agent_manager.run(react.id, task, context)
            return AgentResult(
                success=res.success,
                output={
                    "plan": plan,
                    "execute": res.output,
                    "verify": "delegated-to-react",
                },
                metadata={"experimental": True, "method": "pev-via-react"},
                error=res.error,
            )
        except Exception as e:
            return AgentResult(
                success=False,
                error=str(e),
                metadata={"experimental": True, "plan": plan},
            )
