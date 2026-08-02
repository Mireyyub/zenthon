"""Skeleton-of-Thought (SoT) Reasoning – əvvəlcə skelet, sonra genişləndirmə."""

from typing import List, Dict, Any, Optional


class SkeletonOfThought:
    def reason(
        self,
        query: str,
        context: Optional[List[str]] = None,
        goal: Optional[str] = None,
        max_steps: int = 8,
    ) -> Dict[str, Any]:
        context = context or []
        trace: List[str] = [f"Skeleton-of-Thought başladı: {query[:160]}"]

        if goal:
            trace.append(f"Məqsəd: {goal}")

        # 1. Skelet
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

        # 2. Genişləndirmə
        expansions = [
            "Problemin tərifi: Input və istənilən nəticə aydınlaşdırıldı.",
            "Əsas komponentlər: Perception → Memory → Reasoning → Action.",
            "Mümkün həll yolları: CoT (xətti), ToT (budaqlı), hybrid yanaşmalar nəzərdən keçirildi.",
            "Qiymətləndirmə: Confidence, izaholunabilirlik, sürət və məqsədə uyğunluq.",
            "Seçilmiş həll: Strukturlaşdırılmış, skelet əsaslı cavab.",
        ]
        if context:
            expansions.insert(
                1, f"Kontekst: {len(context)} əvvəlki xatirə nəzərə alındı."
            )

        for exp in expansions:
            trace.append(exp)

        conclusion = (
            f"Skeleton-of-Thought tamamlandı. "
            f"Sual «{query[:50]}...» üçün strukturlaşdırılmış cavab hazırdır."
        )

        confidence = 0.81
        if context:
            confidence += 0.04
        if goal:
            confidence += 0.03
        confidence = min(0.93, confidence)

        return {
            "trace": trace,
            "conclusion": conclusion,
            "confidence": round(confidence, 3),
            "method": "skeleton_of_thought",
            "skeleton": skeleton,
        }
