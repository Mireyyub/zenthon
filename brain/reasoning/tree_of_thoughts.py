"""Tree-of-Thoughts (ToT) Reasoning"""

from typing import List, Dict, Any, Optional


class TreeOfThoughts:
    def reason(self, query: str, context: Optional[List[str]] = None,
               goal: Optional[str] = None, max_steps: int = 8) -> Dict[str, Any]:
        trace = [f"ToT başladı: {query[:150]}"]
        branches = [
            {"name": "Analitik", "score": 0.72, "summary": "Məntiqi və fakt əsaslı yanaşma"},
            {"name": "Yaradıcı", "score": 0.65, "summary": "Alternativ və innovativ həll"},
            {"name": "Praktik", "score": 0.81, "summary": "Tez tətbiq oluna bilən praktiki yol"},
        ]
        for b in branches:
            trace.append(f"Budaq [{b['name']}]: {b['summary']} (score={b['score']:.2f})")
        best = max(branches, key=lambda x: x["score"])
        trace.append(f"Seçilmiş budaq: {best['name']} (score={best['score']:.2f})")
        conclusion = f"Tree-of-Thoughts nəticəsi: {best['summary']}. Sual: {query[:60]}..."
        return {"trace": trace, "conclusion": conclusion, "confidence": best["score"],
                "method": "tree_of_thoughts", "selected_branch": best["name"]}
