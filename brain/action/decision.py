"""Decision Engine"""

from typing import Any, Dict, List, Optional

from core.logger import logger


class DecisionEngine:
    def decide(self, reasoning_result: Dict[str, Any], goal: Optional[str] = None,
               working_memory: Optional[List] = None) -> Dict[str, Any]:
        conclusion = reasoning_result.get("conclusion", "")
        confidence = reasoning_result.get("confidence", 0.0)
        method = reasoning_result.get("method", "unknown")

        if confidence >= 0.75:
            action, message = "execute", "Yüksək etimad. Nəticəni birbaşa istifadə et."
        elif confidence >= 0.5:
            action, message = "verify", "Orta etimad. Əlavə yoxlama tövsiyə olunur."
        else:
            action, message = "rethink", "Aşağı etimad. Fərqli reasoning rejimi ilə yenidən düşün."

        decision = {
            "action": action, "message": message, "confidence": confidence,
            "method_used": method, "conclusion_summary": conclusion[:200],
            "goal_aligned": goal is not None,
        }
        logger.info(f"Decision: {action} (confidence={confidence:.3f})")
        return decision
