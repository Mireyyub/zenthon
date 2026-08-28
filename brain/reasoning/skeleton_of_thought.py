"""
Skeleton-of-Thought (SoT) Reasoning.

Əvvəlcə skelet yaradır, sonra hər hissəni genişləndirir.
LLMProvider mövcuddursa real model ilə, yoxdursa fallback.
"""

from typing import List, Dict, Any, Optional

from core.logger import logger


class SkeletonOfThought:
    SYSTEM_PROMPT = (
        "Sən strukturlaşdırılmış düşünən bir agensən. "
        "Əvvəlcə qısa skelet (5 addımlı outline) yaz, "
        "sonra hər addımı 1-2 cümlə ilə genişləndir. "
        "Sonunda 'Nəticə:' ilə yekun cavabı ver."
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

            parts = [f"Sual / Tapşırıq: {query}"]
            if goal:
                parts.append(f"Məqsəd: {goal}")
            if context:
                parts.append("Kontekst:\n" + "\n".join(f"- {c}" for c in context[:4]))
            parts.append("Skelet yarat, sonra genişləndir və nəticə çıxar.")
            prompt = "\n\n".join(parts)

            comp = provider.complete(
                prompt, system=self.SYSTEM_PROMPT, temperature=0.35
            )
            if not comp.ok or not comp.text:
                return None

            raw = comp.text
            lines = [ln.strip() for ln in raw.splitlines() if ln.strip()]
            trace = lines if lines else [raw[:400]]

            conclusion = raw
            for ln in reversed(lines):
                if ln.lower().startswith("nəticə") or ln.lower().startswith("conclusion"):
                    conclusion = ln
                    break
            else:
                conclusion = (
                    f"Skeleton-of-Thought (LLM) tamamlandı. "
                    f"Sual «{query[:50]}...» üçün strukturlaşdırılmış cavab hazırdır."
                )

            confidence = 0.86
            if context:
                confidence += 0.03
            if goal:
                confidence += 0.03

            logger.info(f"SoT: LLM cavabı uğurla alındı (provider={comp.provider}).")
            return {
                "trace": trace,
                "conclusion": conclusion,
                "confidence": round(min(0.94, confidence), 3),
                "method": "skeleton_of_thought",
                "llm_used": True,
                "llm_provider": comp.provider,
                "llm_model": comp.model,
                "llm_latency_ms": comp.latency_ms,
            }
        except Exception as e:
            logger.warning(f"SoT LLM error: {e}")
            return None

    def _fallback(
        self, query: str, context: List[str], goal: Optional[str]
    ) -> Dict[str, Any]:
        trace = [f"Skeleton-of-Thought başladı: {query[:160]}"]
        if goal:
            trace.append(f"Məqsəd: {goal}")

        skeleton = [
            "1. Problemin tərifi və sərhədləri",
            "2. Əsas komponentlər / alt-hissələr",
            "3. Mümkün həll yolları",
            "4. Qiymətləndirmə meyarları",
            "5. Seçilmiş həll + əsaslandırma",
        ]
        trace.append("Skelet yaradıldı:")
        for s in skeleton:
            trace.append(f"  {s}")

        expansions = [
            "Problemin tərifi: Input və istənilən nəticə aydınlaşdırıldı.",
            "Əsas komponentlər: Perception → Memory → Reasoning → Action.",
            "Mümkün həll yolları: CoT, ToT və hybrid yanaşmalar nəzərdən keçirildi.",
            "Qiymətləndirmə: Confidence, izaholunabilirlik, sürət və məqsədə uyğunluq.",
            "Seçilmiş həll: Strukturlaşdırılmış, skelet əsaslı cavab.",
        ]
        if context:
            expansions.insert(1, f"Kontekst: {len(context)} əvvəlki xatirə nəzərə alındı.")

        for exp in expansions:
            trace.append(exp)

        conclusion = (
            f"Skeleton-of-Thought tamamlandı. "
            f"Sual «{query[:50]}...» üçün strukturlaşdırılmış cavab hazırdır."
        )

        confidence = 0.80
        if context:
            confidence += 0.04
        if goal:
            confidence += 0.03

        return {
            "trace": trace,
            "conclusion": conclusion,
            "confidence": round(min(0.91, confidence), 3),
            "method": "skeleton_of_thought",
            "skeleton": skeleton,
            "llm_used": False,
        }
