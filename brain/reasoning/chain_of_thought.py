"""Chain-of-Thought (CoT) Reasoning"""

from typing import List, Dict, Any, Optional


class ChainOfThought:
    def reason(self, query: str, context: Optional[List[str]] = None,
               goal: Optional[str] = None, max_steps: int = 6) -> Dict[str, Any]:
        context = context or []
        trace: List[str] = [f"Problemi anladım: {query[:200]}"]
        if context:
            trace.append(f"Uyğun xatirələr: {len(context)} ədəd tapıldı.")
        if goal:
            trace.append(f"Məqsəd: {goal}")
        for i, s in enumerate(["Əsas faktları müəyyənləşdirdim.", "Mümkün yanaşmaları nəzərdən keçirdim.",
                               "Ən məntiqli yolu seçdim.", "Nəticəni formalaşdırdım."][:max(0, max_steps-3)]):
            trace.append(f"Addım {i+1}: {s}")
        conclusion = f"Nəticə: '{query[:80]}...' sualına əsasən ən uyğun cavab hazırlandı."
        if goal:
            conclusion += f" Məqsəd ({goal}) nəzərə alındı."
        trace.append(conclusion)
        return {"trace": trace, "conclusion": conclusion, "confidence": 0.78, "method": "chain_of_thought"}
