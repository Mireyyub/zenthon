"""Safe sequential orchestration for registered Leon agents."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from agents.manager import AgentManager, agent_manager


class UnifiedAgentOrchestrator:
    """Runs an explicit allowlisted agent sequence with shared context."""

    def __init__(self, manager: AgentManager = agent_manager):
        self.manager = manager

    def run(self, task: str, agents: Optional[List[str]] = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        sequence = agents or ["react", "coding"]
        shared = dict(context or {})
        steps = []
        for agent_type in sequence:
            agent = self.manager.create(agent_type, allow_experimental=False)
            result = self.manager.run(agent.id, task, shared)
            step = {"agent": agent_type, "success": result.success, "output": result.output, "error": result.error}
            steps.append(step)
            if not result.success:
                return {"ok": False, "task": task, "steps": steps, "context": shared}
            shared[agent_type] = result.output
        return {"ok": True, "task": task, "steps": steps, "context": shared, "output": steps[-1]["output"] if steps else None}


unified_orchestrator = UnifiedAgentOrchestrator()
