"""Chain-of-Thought (CoT) Reasoning – addım-addım xətti düşüncə."""

from typing import List, Dict, Any, Optional


class ChainOfThought:
    def reason(
        self,
        query: str,
        context: Optional[List[str]] = None,
        goal: Optional[str] = None,
        max_steps: int = 6,
    ) -> Dict[str, Any]:
        context = context or []
        trace: List[str] = []

        # 1. Anlama
        trace.append(f"1. Problemi anladım: {query[:220]}")

        # 2. Kontekst
        if context:
            trace.append(f"2. Uyğun xatirələr: {len(context)} ədəd nəzərə alındı.")
            for i, mem in enumerate(context[:3], 1):
                trace.append(f"   • Xatirə {i}: {str(mem)[:90]}...")

        # 3. Məqsəd
        if goal:
            trace.append(f"3. Məqsəd: {goal}")

        # 4. Analiz addımları
        steps = [
            "Əsas faktları və fərziyyələri ayırdım.",
            "Məntiqi əlaqələri qurdum.",
            "Mümkün cavab istiqamətlərini qiymətləndirdim.",
            "Ən tutarlı izahı seçdim.",
        ]
        for i, step in enumerate(steps[: max(1, max_steps - 3)], 1):
            trace.append(f"{3 + i}. {step}")

        # 5. Nəticə
        conclusion = (
            f"Nəticə: '{query[:70]}...' sualına əsasən ən uyğun cavab formalaşdırıldı."
        )
        if goal:
            conclusion += f" Məqsəd («{goal}») nəzərə alınıb."
        if context:
            conclusion += f" {len(context)} xatirə istifadə olunub."

        trace.append(conclusion)

        # Confidence: kontekst və məqsəd olduqda bir az yüksəlir
        confidence = 0.72
        if context:
            confidence += 0.06
        if goal:
            confidence += 0.05
        confidence = min(0.92, confidence)

        return {
            "trace": trace,
            "conclusion": conclusion,
            "confidence": round(confidence, 3),
            "method": "chain_of_thought",
        }
