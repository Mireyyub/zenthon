"""Multimodal Perception Module"""

from typing import Any, Dict, List, Union
import hashlib

from core.logger import logger


class MultimodalPerception:
    def __init__(self):
        self.supported_modalities = ["text", "image", "audio", "multimodal"]

    def process(self, input_data: Union[str, Dict[str, Any], List[Any]]) -> Dict[str, Any]:
        if isinstance(input_data, str):
            return self._process_text(input_data)
        if isinstance(input_data, dict):
            return self._process_dict(input_data)
        if isinstance(input_data, list):
            return self._process_list(input_data)
        return {"modality": "unknown", "summary": str(input_data)[:500], "confidence": 0.5, "features": {}}

    def _process_text(self, text: str) -> Dict[str, Any]:
        text = text.strip()
        summary = text[:300] + ("..." if len(text) > 300 else "")
        return {
            "modality": "text",
            "summary": summary,
            "confidence": 0.95,
            "features": {"length": len(text), "word_count": len(text.split()), "hash": hashlib.md5(text.encode()).hexdigest()[:12]},
            "raw": text,
        }

    def _process_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        modalities, summaries = [], []
        if "text" in data:
            t = self._process_text(str(data["text"]))
            modalities.append("text")
            summaries.append(t["summary"])
        if "image" in data or "image_path" in data:
            modalities.append("image")
            summaries.append("[Image input received]")
        if "audio" in data or "audio_path" in data:
            modalities.append("audio")
            summaries.append("[Audio input received]")
        modality = "multimodal" if len(modalities) > 1 else (modalities[0] if modalities else "unknown")
        return {
            "modality": modality,
            "summary": " | ".join(summaries) if summaries else str(data)[:300],
            "confidence": 0.85,
            "features": {"detected_modalities": modalities},
            "raw": data,
        }

    def _process_list(self, data: List[Any]) -> Dict[str, Any]:
        processed = [self.process(item) for item in data[:10]]
        return {
            "modality": "multimodal",
            "summary": " ; ".join(p["summary"] for p in processed)[:400],
            "confidence": 0.8,
            "features": {"item_count": len(data)},
            "raw": data,
        }
