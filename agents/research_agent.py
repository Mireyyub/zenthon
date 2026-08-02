"""Research Agent – araşdırma, məlumat toplama, xülasə."""

from typing import Any, Dict, Optional

from agents.base import BaseAgent, AgentResult
from core.logger import logger


class ResearchAgent(BaseAgent):
    def __init__(self, name: str = "ResearchAgent", description: str = "Araşdırma və xülasə"):
        super().__init__(name=name, description=description)

    def run(self, task: str, context: Optional[Dict[str, Any]] = None) -> AgentResult:
        logger.info(f"ResearchAgent running: {task[:80]}")
        try:
            from brain import ThinkingBrain
            brain = ThinkingBrain(name="ResearchBrain")
            result = brain.think(
                f"Araşdırma tapşırığı: {task}",
                goal="Dəqiq və strukturlaşdırılmış xülasə",
                reasoning_mode="tot",
            )
            return AgentResult(
                success=True,
                output=result.get("conclusion"),
                metadata={
                    "confidence": result.get("confidence"),
                    "modes_tried": result.get("modes_tried"),
                },
            )
        except Exception as e:
            return AgentResult(success=False, error=str(e))
