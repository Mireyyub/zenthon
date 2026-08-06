"""Reflexion Agent – EXPERIMENTAL reflect-retry via ReasoningEngine."""

from __future__ import annotations

from typing import Any, Dict, Optional

from agents.base import BaseAgent, AgentResult


class ReflexionAgent(BaseAgent):
    PRODUCTION = False

    def __init__(self, name: str = "ReflexionAgent", description: str = "Experimental reflexion"):
        super().__init__(name=name, description=description)

    def run(self, task: str, context: Optional[Dict[str, Any]] = None) -> AgentResult:
        try:
            from brain.reasoning.engine import ReasoningEngine

            eng = ReasoningEngine(persist_traces=True)
            first = eng.reason(task, use_brain=True)
            conf = float(first.get("confidence") or 0)
            if conf >= 0.7 and first.get("validation") == "ok":
                return AgentResult(
                    success=True,
                    output=first.get("answer"),
                    metadata={
                        "experimental": True,
                        "rounds": 1,
                        "trace_id": first.get("trace_id"),
                        "confidence": conf,
                    },
                )
            # one reflection pass
            reflect_q = (
                f"Əvvəlki cavab zəif idi ({first.get('answer')}). "
                f"Yenidən düşün: {task}"
            )
            second = eng.reason(reflect_q, use_brain=True)
            return AgentResult(
                success=True,
                output=second.get("answer") or first.get("answer"),
                metadata={
                    "experimental": True,
                    "rounds": 2,
                    "first_confidence": conf,
                    "second_confidence": second.get("confidence"),
                    "trace_ids": [first.get("trace_id"), second.get("trace_id")],
                },
            )
        except Exception as e:
            return AgentResult(success=False, error=str(e), metadata={"experimental": True})
