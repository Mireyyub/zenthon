"""Vision Agent – EXPERIMENTAL stub (no real vision pipeline)."""

from __future__ import annotations

from typing import Any, Dict, Optional

from agents.base import BaseAgent, AgentResult


class VisionAgent(BaseAgent):
    PRODUCTION = False

    def __init__(self, name: str = "VisionAgent", description: str = "Experimental vision stub"):
        super().__init__(name=name, description=description)

    def run(self, task: str, context: Optional[Dict[str, Any]] = None) -> AgentResult:
        return AgentResult(
            success=False,
            error="Vision pipeline not implemented. Experimental stub only.",
            metadata={
                "experimental": True,
                "task": (task or "")[:120],
                "hint": "Integrate real VLM separately; do not treat this as production.",
            },
        )
