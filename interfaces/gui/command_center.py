"""Deterministic, display-independent helpers for the Zenthon Command Center."""

from __future__ import annotations


def infer_operation_mode(query: str) -> str:
    """Return a transparent mission label without requiring a GUI runtime."""
    normalized = query.casefold()
    if any(term in normalized for term in ("kod", "python", "typescript", "javascript", "function", "class")):
        return "Code Operation"
    if any(term in normalized for term in ("xülasə", "özet", "summar", "qısalt")):
        return "Summary Operation"
    if any(term in normalized for term in ("analiz", "analy", "araşdır", "incele")):
        return "Analysis Operation"
    if any(term in normalized for term in ("tərcümə", "çevir", "translate", "ingiliscə", "türkçə")):
        return "Translation Operation"
    if any(term in normalized for term in ("şəkil", "görüntü", "image", "səs", "audio", "sənəd", "belge", "pdf")):
        return "Multimodal Operation"
    return "Reasoning Operation"
