"""
Decision Engine — brain.confidence ilə vahid formula (Faza 3).
"""

from typing import Any, Dict, List, Optional

from core.logger import logger
from brain.confidence import composite_confidence, action_from_confidence


class DecisionEngine:
    def decide(
        self,
        reasoning_result: Dict[str, Any],
        goal: Optional[str] = None,
        working_memory: Optional[List] = None,
        uncertainty: float = 0.0,
        evidence_quality: Optional[float] = None,
        source_reliability: Optional[float] = None,
    ) -> Dict[str, Any]:
        # Artıq reasoning_engine decision veribsə — uyğunlaşdır
        if reasoning_result.get("decision") and "action" in (reasoning_result.get("decision") or {}):
            d = dict(reasoning_result["decision"])
            d.setdefault("conclusion_summary", str(reasoning_result.get("conclusion") or reasoning_result.get("answer") or "")[:240])
            d.setdefault("method_used", reasoning_result.get("reasoning_mode") or reasoning_result.get("strategy"))
            return d

        conclusion = reasoning_result.get("conclusion") or reasoning_result.get("answer") or ""
        confidence = float(reasoning_result.get("confidence", 0.0))
        method = reasoning_result.get("method") or reasoning_result.get("reasoning_mode") or "unknown"
        source = reasoning_result.get("source") or "unknown"

        eq = evidence_quality if evidence_quality is not None else (
            0.8 if reasoning_result.get("evidence") else 0.45
        )
        sr = source_reliability if source_reliability is not None else 0.7

        pack = composite_confidence(
            base=confidence,
            evidence_quality=eq,
            source_reliability=sr,
            consistency=0.85 if conclusion and str(conclusion) != "UNKNOWN" else 0.25,
            method=str(source).split(":")[0] if source != "unknown" else method,
            has_goal=goal is not None,
            memory_hits=len(working_memory or []),
            uncertainty=uncertainty,
        )
        action = action_from_confidence(pack["score"])
        decision = {
            **action,
            "confidence": pack["score"],
            "confidence_label": pack["label"],
            "composite_score": pack["score"],
            "uncertainty": round(uncertainty, 3),
            "method_used": method,
            "conclusion_summary": str(conclusion)[:240],
            "goal_aligned": goal is not None,
            "scores": pack.get("components") or {},
            "composite": pack,
        }
        logger.info(
            f"Decision → {decision['action']} | composite={pack['score']:.3f} | method={method}"
        )
        return decision
