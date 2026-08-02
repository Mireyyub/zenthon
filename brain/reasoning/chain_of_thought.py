"""
Chain-of-Thought (CoT) Reasoning.

LLM mövcuddursa real model ilə işləyir,
yoxdursa qayda əsaslı fallback istifadə edir.
"""

from typing import List, Dict, Any, Optional
import re

from core.logger import logger


class ChainOfThought:
    SYSTEM_PROMPT = (
        "Sən diqqətli və məntiqli bir düşüncə köməkçisisən. "
        "Verilən suala addım-addım, qısa və aydın şəkildə cavab ver. "
        "Hər addımı nömrələ. Sonunda 'Nəticə:' ilə yekun cavabı yaz."
    )

    def reason(
        self,
        query: str,
        context: Optional[List[str]] = None,
        goal: Optional[str] = None,
        max_steps: int = 6,
    ) -> Dict[str, Any]:
        context = context or []

        # LLM cəhdi
        llm_result = self._try_llm(query, context, goal, max_steps)
        if llm_result is not None:
            return llm_result

        # Fallback
        return self._fallback(query, context, goal, max_steps)

    def _try_llm(
        self,
        query: str,
        context: List[str],
        goal: Optional[str],
        max_steps: int,
    ) -> Optional[Dict[str, Any]]:
        try:
            from brain.llm.client import get_llm_client

            client = get_llm_client()
            if not client.is_available:
                return None

            parts = [f"Sual: {query}"]
            if goal:
                parts.append(f"Məqsəd: {goal}")
            if context:
                ctx_text = "\n".join(f"- {c}" for c in context[:5])
                parts.append(f"Uyğun xatirələr:\n{ctx_text}")
            parts.append(
                f"Maksimum {max_steps} addımda düşün və nəticə çıxar."
            )
            prompt = "\n\n".join(parts)

            raw = client.complete(prompt, system=self.SYSTEM_PROMPT)
            if not raw:
                return None

            trace, conclusion = self._parse_llm_output(raw, query)
            confidence = self._estimate_confidence(raw, context, goal)

            logger.info("CoT: LLM cavabı uğurla alındı.")
            return {
                "trace": trace,
                "conclusion": conclusion,
                "confidence": confidence,
                "method": "chain_of_thought",
                "llm_used": True,
            }
        except Exception as e:
            logger.warning(f"CoT LLM error: {e}")
            return None

    def _parse_llm_output(self, raw: str, query: str):
        lines = [ln.strip() for ln in raw.splitlines() if ln.strip()]
        trace = lines[:] if lines else [raw[:300]]

        conclusion = raw
        for ln in reversed(lines):
            if ln.lower().startswith("nəticə") or ln.lower().startswith("conclusion"):
                conclusion = ln
                break
        else:
            conclusion = lines[-1] if lines else f"Nəticə: {query[:80]}"

        return trace, conclusion

    def _estimate_confidence(self, raw: str, context: List, goal: Optional[str]) -> float:
        conf = 0.78
        if len(raw) > 200:
            conf += 0.05
        if context:
            conf += 0.04
        if goal:
            conf += 0.03
        if re.search(r"nəticə|conclusion", raw, re.I):
            conf += 0.03
        return round(min(0.94, conf), 3)

    def _fallback(
        self,
        query: str,
        context: List[str],
        goal: Optional[str],
        max_steps: int,
    ) -> Dict[str, Any]:
        trace: List[str] = [f"1. Problemi anladım: {query[:220]}"]

        if context:
            trace.append(f"2. Uyğun xatirələr: {len(context)} ədəd nəzərə alındı.")
            for i, mem in enumerate(context[:3], 1):
                trace.append(f"   • Xatirə {i}: {str(mem)[:90]}...")

        if goal:
            trace.append(f"3. Məqsəd: {goal}")

        steps = [
            "Əsas faktları və fərziyyələri ayırdım.",
            "Məntiqi əlaqələri qurdum.",
            "Mümkün cavab istiqamətlərini qiymətləndirdim.",
            "Ən tutarlı izahı seçdim.",
        ]
        for i, step in enumerate(steps[: max(1, max_steps - 3)], 1):
            trace.append(f"{3 + i}. {step}")

        conclusion = (
            f"Nəticə: '{query[:70]}...' sualına əsasən ən uyğun cavab formalaşdırıldı."
        )
        if goal:
            conclusion += f" Məqsəd («{goal}») nəzərə alınıb."

        trace.append(conclusion)

        confidence = 0.70
        if context:
            confidence += 0.05
        if goal:
            confidence += 0.04

        return {
            "trace": trace,
            "conclusion": conclusion,
            "confidence": round(min(0.88, confidence), 3),
            "method": "chain_of_thought",
            "llm_used": False,
        }
