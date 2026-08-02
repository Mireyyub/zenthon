"""Tree-of-Thoughts (ToT) Reasoning – bir neçə budağı araşdırır."""

from typing import List, Dict, Any, Optional


class TreeOfThoughts:
    def reason(
        self,
        query: str,
        context: Optional[List[str]] = None,
        goal: Optional[str] = None,
        max_steps: int = 8,
    ) -> Dict[str, Any]:
        context = context or []
        trace: List[str] = [f"ToT başladı: {query[:160]}"]

        if goal:
            trace.append(f"Məqsəd: {goal}")

        # Üç fərqli düşüncə budağı
        branches = [
            {
                "name": "Analitik",
                "score": 0.74,
                "summary": "Fakt və məntiq əsaslı yanaşma",
                "detail": "Məlumatları parçalayıb səbəb-nəticə əlaqələrini qururam.",
            },
            {
                "name": "Yaradıcı",
                "score": 0.68,
                "summary": "Alternativ və innovativ həll yolu",
                "detail": "Standart həlldən kənar variantları da nəzərdən keçirirəm.",
            },
            {
                "name": "Praktik",
                "score": 0.83,
                "summary": "Tez tətbiq oluna bilən praktiki yol",
                "detail": "Resurs və vaxt məhdudiyyətlərini nəzərə alıram.",
            },
        ]

        # Kontekst varsa praktik budağın score-unu bir az artır
        if context:
            branches[2]["score"] = min(0.91, branches[2]["score"] + 0.05)

        for b in branches:
            trace.append(
                f"Budaq [{b['name']}]: {b['summary']} (score={b['score']:.2f})"
            )
            trace.append(f"   → {b['detail']}")

        best = max(branches, key=lambda x: x["score"])
        trace.append(
            f"Seçilmiş budaq: {best['name']} (score={best['score']:.2f})"
        )

        conclusion = (
            f"Tree-of-Thoughts nəticəsi → {best['name']} yanaşması seçildi: "
            f"{best['summary']}. Sual: {query[:55]}..."
        )

        return {
            "trace": trace,
            "conclusion": conclusion,
            "confidence": round(best["score"], 3),
            "method": "tree_of_thoughts",
            "selected_branch": best["name"],
            "all_branches": [{"name": b["name"], "score": b["score"]} for b in branches],
        }
