"""Voice Agent – EXPERIMENTAL stub (no STT/TTS)."""

from __future__ import annotations

from typing import Any, Dict, Optional

from agents.base import BaseAgent, AgentResult


class VoiceAgent(BaseAgent):
    PRODUCTION = False

    def __init__(self, name: str = "VoiceAgent", description: str = "Experimental voice stub"):
        super().__init__(name=name, description=description)

    def run(self, task: str, context: Optional[Dict[str, Any]] = None) -> AgentResult:
        return AgentResult(
            success=False,
            error="Voice STT/TTS not implemented. Experimental stub only.",
            metadata={
                "experimental": True,
                "task": (task or "")[:120],
                "hint": "Wire Whisper/TTS externally; not part of cognitive core.",
            },
        )
