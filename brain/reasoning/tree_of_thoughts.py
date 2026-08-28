"""
Tree-of-Thoughts (ToT) Reasoning.

LLMProvider ilə bir neçə budaq generasiya edir, yoxdursa fallback.
"""

from typing import List, Dict, Any, Optional

from core.logger import logger


class TreeOfThoughts:
    SYSTEM_PROMPT = (
        "Sən yaradıcı və analitik düşünən bir agensən. "
        "Verilən suala 3 fərqli yanaşma (budaq) təklif et. "
        "Hər budaq üçün: ad, qısa izah, üstünlük və zəif tərəf yaz. "
        "Sonunda ən yaxşı budağı seç və 'Seçilmiş:' ilə başla."
    )

    def reason(
        self,
        query: str,
        context: Optional[List[str]] = None,
        goal: Optional[str] = None,
        max_steps: int = 8,
    ) -> Dict[str, Any]:
        context = context or []

        llm_result = self._try_llm(query, context, goal)
        if llm_result is not None:
            return llm_result

        return self._fallback(query, context, goal)

    def _try_llm(
        self, query: str, context: List[str], goal: Optional[str]
    ) -> Optional[Dict[str, Any]]:
        try:
            from brain.llm.provider import get_llm_provider

            provider = get_llm_provider()
            if not provider.is_available:
                return None

            parts = [f"Sual: {query}"]
            if goal:
                parts.append(f"Məqsəd: {goal}")
            if context:
                parts.append("Kontekst:\n" + "\n".join(f"- {c}" for c in context[:4]))
            parts.append("3 fərqli budaq yarat və ən yaxşısını seç.")
            prompt = "\n\n".join(parts)

            comp = provider.complete(
                prompt, system=self.SYSTEM_PROMPT, temperature=0.6
            )
            if not comp.ok or not comp.text:
                return None

            raw = comp.text
            trace = [ln.strip() for ln in raw.splitlines() if ln.strip()]
            if not trace:
                trace = [raw[:400]]

            selected = "Praktik"
            for ln in trace:
                if "seçilmiş" in ln.lower() or "selected" in ln.lower():
                    selected = ln
                    break

            conclusion = (
                f"Tree-of-Thoughts (LLM) nəticəsi. Seçilmiş istiqamət: {selected[:80]}. "
                f"Sual: {query[:50]}..."
            )

            confidence = 0.84
            if context:
                confidence += 0.03
            if goal:
                confidence += 0.03

            logger.info(f"ToT: LLM cavabı uğurla alındı (provider={comp.provider}).")
            return {
                "trace": trace,
                "conclusion": conclusion,
                "confidence": round(min(0.93, confidence), 3),
                "method": "tree_of_thoughts",
                "selected_branch": selected[:60],
                "llm_used": True,
                "llm_provider": comp.provider,
                "llm_model": comp.model,
                "llm_latency_ms": comp.latency_ms,
            }
        except Exception as e:
            logger.warning(f"ToT LLM error: {e}")
            return None

    def _fallback(
        self, query: str, context: List[str], goal: Optional[str]
    ) -> Dict[str, Any]:
        trace = [f"ToT başladı: {query[:160]}"]
        if goal:
            trace.append(f"Məqsəd: {goal}")

        branches = [
            {"name": "Analitik", "score": 0.74, "summary": "Fakt və məntiq əsaslı yanaşma"},
            {"name": "Yaradıcı", "score": 0.68, "summary": "Alternativ və innovativ həll yolu"},
            {"name": "Praktik", "score": 0.83, "summary": "Tez tətbiq oluna bilən praktiki yol"},
        ]
        if context:
            branches[2]["score"] = min(0.91, branches[2]["score"] + 0.05)

        for b in branches:
            trace.append(f"Budaq [{b['name']}]: {b['summary']} (score={b['score']:.2f})")

        best = max(branches, key=lambda x: x["score"])
        trace.append(f"Seçilmiş budaq: {best['name']} (score={best['score']:.2f})")

        conclusion = (
            f"Tree-of-Thoughts nəticəsi → {best['name']}: {best['summary']}. "
            f"Sual: {query[:55]}..."
        )

        return {
            "trace": trace,
            "conclusion": conclusion,
            "confidence": round(best["score"], 3),
            "method": "tree_of_thoughts",
            "selected_branch": best["name"],
            "llm_used": False,
        }
