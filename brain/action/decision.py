"""
Gücləndirilmiş Decision Engine.

Multi-criteria qərar:
- Confidence
- Uncertainty
- Goal alignment
- Method reliability
- Risk level
"""

from typing import Any, Dict, List, Optional

from core.logger import logger


class DecisionEngine:
    """Reasoning nəticəsinə əsasən ağıllı qərar verir."""

    METHOD_RELIABILITY = {
        "chain_of_thought": 0.78,
        "tree_of_thoughts": 0.82,
        "skeleton_of_thought": 0.85,
        "unknown": 0.60,
    }

    def decide(
        self,
        reasoning_result: Dict[str, Any],
        goal: Optional[str] = None,
        working_memory: Optional[List] = None,
        uncertainty: float = 0.0,
    ) -> Dict[str, Any]:
        conclusion = reasoning_result.get("conclusion", "")
        confidence = float(reasoning_result.get("confidence", 0.0))
        method = reasoning_result.get("method", "unknown")
        method_rel = self.METHOD_RELIABILITY.get(method, 0.60)

        # Composite score
        goal_bonus = 0.08 if goal else 0.0
        memory_bonus = 0.04 if working_memory and len(working_memory) > 2 else 0.0
        unc_penalty = uncertainty * 0.15

        composite = (
            confidence * 0.55
            + method_rel * 0.25
            + goal_bonus
            + memory_bonus
            - unc_penalty
        )
        composite = max(0.0, min(1.0, composite))

        # Action selection
        if composite >= 0.80:
            action = "execute"
            message = "Yüksək etimad və sabit reasoning. Nəticəni birbaşa istifadə et."
            priority = "high"
            risk = "low"
        elif composite >= 0.62:
            action = "verify"
            message = "Orta etimad. Əlavə yoxlama və ya ikinci perspektiv tövsiyə olunur."
            priority = "medium"
            risk = "medium"
        else:
            action = "rethink"
            message = "Aşağı etimad / yüksək qeyri-müəyyənlik. Fərqli reasoning rejimi ilə yenidən düşün."
            priority = "low"
            risk = "high"

        decision = {
            "action": action,
            "message": message,
            "priority": priority,
            "risk": risk,
            "confidence": round(confidence, 3),
            "composite_score": round(composite, 3),
            "uncertainty": round(uncertainty, 3),
            "method_used": method,
            "method_reliability": method_rel,
            "conclusion_summary": conclusion[:240],
            "goal_aligned": goal is not None,
            "suggested_next": self._suggest_next(action, method),
            "scores": {
                "raw_confidence": round(confidence, 3),
                "method_reliability": method_rel,
                "goal_bonus": goal_bonus,
                "memory_bonus": memory_bonus,
                "uncertainty_penalty": round(unc_penalty, 3),
            },
        }

        logger.info(
            f"Decision → {action} | composite={composite:.3f} | "
            f"conf={confidence:.3f} | risk={risk} | method={method}"
        )
        return decision

    def _suggest_next(self, action: str, current_method: str) -> str:
        if action == "execute":
            return "Nəticəni istifadə et və ya növbəti tapşırığa keç."
        if action == "verify":
            return "Eyni sualı fərqli mode ilə (məs: sot və ya tot) yenidən soruş və müqayisə et."
        alternatives = {"cot": "tot", "tot": "sot", "sot": "cot"}
        alt = alternatives.get(
            current_method.replace("chain_of_thought", "cot")
            .replace("tree_of_thoughts", "tot")
            .replace("skeleton_of_thought", "sot"),
            "tot",
        )
        return f"reasoning_mode='{alt}' ilə think() çağır və nəticələri müqayisə et."
