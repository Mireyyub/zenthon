"""Confidence Model (spec 007)."""

from __future__ import annotations

from typing import Dict

LEVELS = {
    0.00: "Unknown",
    0.25: "Weak",
    0.50: "Possible",
    0.75: "Strong",
    1.00: "Verified",
}


def label_confidence(score: float) -> str:
    score = max(0.0, min(1.0, float(score)))
    best = "Unknown"
    best_k = -1.0
    for k, name in LEVELS.items():
        if score >= k and k >= best_k:
            best_k = k
            best = name
    return best


def compute_confidence(
    evidence_quality: float = 0.5,
    source_reliability: float = 0.5,
    consistency: float = 0.5,
) -> Dict[str, float | str]:
    raw = max(0.0, min(1.0, evidence_quality * source_reliability * consistency))
    return {
        "score": round(raw, 3),
        "label": label_confidence(raw),
        "evidence_quality": evidence_quality,
        "source_reliability": source_reliability,
        "consistency": consistency,
    }
