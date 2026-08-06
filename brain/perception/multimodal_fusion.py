"""Multimodal fusion – honest stub (no real vision/audio models)."""

from __future__ import annotations

from typing import Any, Dict, List, Optional


class MultimodalFusion:
    """Placeholder. Leon cognitive core is text-first."""

    SUPPORTED = ("text",)

    def fuse(
        self,
        text: Optional[str] = None,
        image: Any = None,
        audio: Any = None,
        **kwargs,
    ) -> Dict[str, Any]:
        modalities_present = []
        if text:
            modalities_present.append("text")
        if image is not None:
            modalities_present.append("image")
        if audio is not None:
            modalities_present.append("audio")

        if image is not None or audio is not None:
            return {
                "ok": False,
                "fused_text": text or "",
                "modalities": modalities_present,
                "error": "Image/audio fusion not implemented. Text-only path active.",
                "experimental": True,
            }

        return {
            "ok": True,
            "fused_text": text or "",
            "modalities": modalities_present or ["text"],
            "experimental": False,
        }

    def status(self) -> Dict[str, Any]:
        return {
            "supported": list(self.SUPPORTED),
            "image": False,
            "audio": False,
            "note": "Cognitive core is text-first; multimodal is experimental/future",
        }
