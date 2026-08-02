"""Voice Agent – səs/audio emalı placeholder."""

from typing import Any, Dict, Optional

from agents.base import BaseAgent, AgentResult
from core.logger import logger


class VoiceAgent(BaseAgent):
    def __init__(self, name: str = "VoiceAgent", description: str = "Səs tanıma və sintez"):
        super().__init__(name=name, description=description)

    def run(self, task: str, context: Optional[Dict[str, Any]] = None) -> AgentResult:
        logger.info(f"VoiceAgent: {task[:80]}")
        context = context or {}
        audio_path = context.get("audio_path") or context.get("audio")

        try:
            from brain import ThinkingBrain
            brain = ThinkingBrain(name="VoiceBrain")
            input_data = {"text": task}
            if audio_path:
                input_data["audio_path"] = audio_path
            result = brain.think(
                input_data,
                goal="Audio məlumatı ilə birlikdə cavab ver",
                reasoning_mode="cot",
            )
            return AgentResult(
                success=True,
                output=result.get("conclusion"),
                metadata={
                    "modality": result.get("modality"),
                    "confidence": result.get("confidence"),
                    "audio": audio_path,
                },
            )
        except Exception as e:
            return AgentResult(success=False, error=str(e))
