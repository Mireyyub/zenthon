"""
Confidence Model (spec 007) + Decision composite (vahid formula).
"""

from __future__ import annotations

from typing import Any, Dict, Optional

LEVELS = {
    0.00: "Unknown",
    0.25: "Weak",
    0.50: "Possible",
    0.75: "Strong",
    1.00: "Verified",
}

METHOD_RELIABILITY = {
    "curriculum": 0.92,
    "facts": 0.85,
    "graph": 0.82,
    "deduction": 0.80,
    "chain_of_thought": 0.78,
    "tree_of_thoughts": 0.82,
    "skeleton_of_thought": 0.85,
    "induction": 0.72,
    "abduction": 0.70,
    "analogy": 0.68,
    "llm": 0.65,
    "unknown": 0.50,
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
) -> Dict[str, Any]:
    """Spec 007 product model."""
    raw = max(0.0, min(1.0, evidence_quality * source_reliability * consistency))
    return {
        "score": round(raw, 3),
        "label": label_confidence(raw),
        "evidence_quality": evidence_quality,
        "source_reliability": source_reliability,
        "consistency": consistency,
    }


def composite_confidence(
    *,
    base: float = 0.5,
    evidence_quality: float = 0.5,
    source_reliability: float = 0.5,
    consistency: float = 0.5,
    method: str = "unknown",
    has_goal: bool = False,
    memory_hits: int = 0,
    uncertainty: float = 0.0,
) -> Dict[str, Any]:
    """
    Vahid formula — ReasoningEngine + DecisionEngine eyni.
    0.5 * product(evidence, source, consistency) + 0.5 * base
    + method reliability blend + goal/memory bonuses - uncertainty
    """
    product = evidence_quality * source_reliability * consistency
    blended = 0.5 * product + 0.5 * max(0.0, min(1.0, base))
    method_rel = METHOD_RELIABILITY.get(method, METHOD_RELIABILITY["unknown"])
    # pull slightly toward method reliability
    score = 0.7 * blended + 0.3 * method_rel
    if has_goal:
        score += 0.04
    if memory_hits > 0:
        score += min(0.06, 0.02 * memory_hits)
    score -= uncertainty * 0.15
    score = max(0.0, min(1.0, score))
    return {
        "score": round(score, 3),
        "label": label_confidence(score),
        "product": round(product, 3),
        "method_reliability": method_rel,
        "components": {
            "base": base,
            "evidence_quality": evidence_quality,
            "source_reliability": source_reliability,
            "consistency": consistency,
            "method": method,
            "uncertainty": uncertainty,
        },
    }


def action_from_confidence(score: float) -> Dict[str, str]:
    if score >= 0.80:
        return {
            "action": "execute",
            "priority": "high",
            "risk": "low",
            "message": "Yüksək etimad. Nəticəni birbaşa istifadə et.",
        }
    if score >= 0.62:
        return {
            "action": "verify",
            "priority": "medium",
            "risk": "medium",
            "message": "Orta etimad. Əlavə yoxlama tövsiyə olunur.",
        }
    return {
        "action": "rethink",
        "priority": "low",
        "risk": "high",
        "message": "Aşağı etimad / UNKNOWN. Fərqli strategy və ya daha çox evidence lazımdır.",
    }
