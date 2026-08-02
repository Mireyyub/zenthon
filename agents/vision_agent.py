"""Vision Agent – şəkil analizi (placeholder + brain inteqrasiyası)."""

from typing import Any, Dict, Optional

from agents.base import BaseAgent, AgentResult
from core.logger import logger


class VisionAgent(BaseAgent):
    def __init__(self, name: str = "VisionAgent", description: str = "Şəkil analizi və obyekt tanıma"):
        super().__init__(name=name, description=description)

    def run(self, task: str, context: Optional[Dict[str, Any]] = None) -> AgentResult:
        logger.info(f"VisionAgent: {task[:80]}")
        context = context or {}
        image_path = context.get("image_path") or context.get("image")

        # Multimodal perception vasitəsilə
        try:
            from brain import ThinkingBrain
            brain = ThinkingBrain(name="VisionBrain")
            input_data = {"text": task}
            if image_path:
                input_data["image_path"] = image_path
            result = brain.think(
                input_data,
                goal="Şəkili və mətni birlikdə analiz et",
                reasoning_mode="cot",
            )
            return AgentResult(
                success=True,
                output=result.get("conclusion"),
                metadata={
                    "modality": result.get("modality"),
                    "confidence": result.get("confidence"),
                    "image": image_path,
                },
            )
        except Exception as e:
            return AgentResult(success=False, error=str(e))
