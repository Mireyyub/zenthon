"""Coding Agent – kod yaratma, analiz, debug."""

from typing import Any, Dict, Optional

from agents.base import BaseAgent, AgentResult
from core.logger import logger


class CodingAgent(BaseAgent):
    def __init__(self, name: str = "CodingAgent", description: str = "Kod yazır, analiz edir, debug edir"):
        super().__init__(name=name, description=description)

    def run(self, task: str, context: Optional[Dict[str, Any]] = None) -> AgentResult:
        logger.info(f"CodingAgent running: {task[:80]}")
        context = context or {}

        # Brain vasitəsilə düşün
        try:
            from brain import ThinkingBrain
            brain = ThinkingBrain(name="CodingBrain")
            result = brain.think(
                f"Kod tapşırığı: {task}",
                goal="İşlək və təmiz kod həlli",
                reasoning_mode="sot",
            )
            return AgentResult(
                success=True,
                output=result.get("conclusion"),
                metadata={
                    "trace": result.get("trace", [])[-5:],
                    "confidence": result.get("confidence"),
                    "mode": result.get("reasoning_mode"),
                },
            )
        except Exception as e:
            return AgentResult(success=False, error=str(e))
