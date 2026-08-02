"""Coding Agent – kod yaratma, analiz, debug + tool istifadəsi."""

from typing import Any, Dict, Optional

from agents.base import BaseAgent, AgentResult
from core.logger import logger


class CodingAgent(BaseAgent):
    def __init__(self, name: str = "CodingAgent", description: str = "Kod yazır, analiz edir, debug edir"):
        super().__init__(name=name, description=description)

    def run(self, task: str, context: Optional[Dict[str, Any]] = None) -> AgentResult:
        logger.info(f"CodingAgent: {task[:80]}")
        context = context or {}

        try:
            from brain import ThinkingBrain
            from models.router import ModelRouter

            router = ModelRouter()
            model = router.select("coding", prefer_local=True)

            # Prefer coding-oriented model via env if possible
            try:
                from brain.llm.client import use_ollama
                if model.provider == "ollama":
                    use_ollama(model.name)
            except Exception:
                pass

            brain = ThinkingBrain(name="CodingBrain")
            result = brain.think(
                f"Kod tapşırığı: {task}\n\nYalnız kod və qısa izah ver.",
                goal="İşlək, təmiz və oxunaqlı kod",
                reasoning_mode="sot",
            )

            # Optional: write to file if path given
            output_path = context.get("output_path")
            if output_path and result.get("conclusion"):
                try:
                    from tools.registry import tool_registry
                    tool_registry.call("write_file", path=output_path, content=str(result["conclusion"]))
                except Exception as e:
                    logger.warning(f"Could not write file: {e}")

            return AgentResult(
                success=True,
                output=result.get("conclusion"),
                metadata={
                    "trace": result.get("trace", [])[-5:],
                    "confidence": result.get("confidence"),
                    "mode": result.get("reasoning_mode"),
                    "model": model.name,
                    "llm_used": result.get("llm_used"),
                    "reflection": result.get("reflection"),
                },
            )
        except Exception as e:
            return AgentResult(success=False, error=str(e))
