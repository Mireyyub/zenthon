"""Decision Engine – reasoning nəticəsinə əsasən qərar verir."""

from typing import Any, Dict, List, Optional

from core.logger import logger


class DecisionEngine:
    def decide(
        self,
        reasoning_result: Dict[str, Any],
        goal: Optional[str] = None,
        working_memory: Optional[List] = None,
    ) -> Dict[str, Any]:
        conclusion = reasoning_result.get("conclusion", "")
        confidence = float(reasoning_result.get("confidence", 0.0))
        method = reasoning_result.get("method", "unknown")

        # Qərar məntiqi
        if confidence >= 0.80:
            action = "execute"
            message = "Yüksək etimad. Nəticəni birbaşa istifadə etmək olar."
            priority = "high"
        elif confidence >= 0.60:
            action = "verify"
            message = "Orta etimad. Əlavə yoxlama və ya ikinci reasoning tövsiyə olunur."
            priority = "medium"
        else:
            action = "rethink"
            message = "Aşağı etimad. Fərqli reasoning rejimi (tot/sot) ilə yenidən düşün."
            priority = "low"

        # Məqsəd uyğunluğu
        goal_aligned = goal is not None

        decision = {
            "action": action,
            "message": message,
            "priority": priority,
            "confidence": round(confidence, 3),
            "method_used": method,
            "conclusion_summary": conclusion[:220],
            "goal_aligned": goal_aligned,
            "suggested_next": self._suggest_next(action, method),
        }

        logger.info(
            f"Decision → {action} | confidence={confidence:.3f} | method={method}"
        )
        return decision

    def _suggest_next(self, action: str, current_method: str) -> str:
        if action == "execute":
            return "Nəticəni istifadə et və ya növbəti tapşırığa keç."
        if action == "verify":
            return "Eyni sualı fərqli mode ilə (məs: sot) yenidən soruş."
        # rethink
        alternatives = {"cot": "tot", "tot": "sot", "sot": "cot"}
        alt = alternatives.get(current_method, "tot")
        return f"reasoning_mode='{alt}' ilə yenidən think() çağır."
