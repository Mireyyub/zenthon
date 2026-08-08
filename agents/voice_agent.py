"""Voice Agent – STT/TTS via multimodal.audio when backends exist."""

from __future__ import annotations

from typing import Any, Dict, Optional

from agents.base import BaseAgent, AgentResult


class VoiceAgent(BaseAgent):
    PRODUCTION = False

    def __init__(self, name: str = "VoiceAgent", description: str = "Speech understand/generate"):
        super().__init__(name=name, description=description)

    def run(self, task: str, context: Optional[Dict[str, Any]] = None) -> AgentResult:
        ctx = context or {}
        mode = (ctx.get("mode") or "auto").lower()
        path = ctx.get("path") or ctx.get("audio_path")
        text = ctx.get("text") or ""

        # Parse simple directives from task
        t = (task or "").strip()
        low = t.lower()
        if not path and ("|" in t or low.startswith("stt:") or low.startswith("file:")):
            # stt:/path or file:/path
            for prefix in ("stt:", "file:", "path:"):
                if low.startswith(prefix):
                    path = t[len(prefix) :].strip()
                    mode = "stt"
                    break

        if mode == "auto":
            if path:
                mode = "stt"
            elif text or t:
                mode = "tts"
                text = text or t

        try:
            from multimodal.audio import audio_available, understand_speech, generate_speech

            if mode == "status":
                return AgentResult(success=True, output=audio_available())

            if mode == "stt":
                if not path:
                    return AgentResult(
                        success=False,
                        error="STT needs path (context path= or task stt:/file.wav)",
                        metadata={"experimental": True},
                    )
                r = understand_speech(path)
                return AgentResult(
                    success=bool(r.get("ok")),
                    output=r.get("transcript") or r,
                    error=None if r.get("ok") else r.get("error"),
                    metadata={"experimental": True, "backend": r.get("backend"), "raw": r},
                )

            if mode == "tts":
                r = generate_speech(text or t, out_path=ctx.get("out_path"))
                return AgentResult(
                    success=bool(r.get("ok")),
                    output=r,
                    error=None if r.get("ok") else r.get("error"),
                    metadata={"experimental": True, "backend": r.get("backend")},
                )

            return AgentResult(
                success=True,
                output=audio_available(),
                metadata={"experimental": True, "hint": "mode=stt|tts|status"},
            )
        except Exception as e:
            return AgentResult(
                success=False,
                error=str(e),
                metadata={"experimental": True},
            )
