"""
Gücləndirilmiş Long-Term Memory.

- Importance scoring
- Access frequency
- Sadə decay (köhnə + az istifadə olunanlar)
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import hashlib


class LongTermMemory:
    def __init__(self, max_items: int = 2000):
        self._store: Dict[str, Dict[str, Any]] = {}
        self.max_items = max_items

    def store(
        self,
        key: str,
        value: Any,
        metadata: Optional[Dict] = None,
        importance: float = 0.5,
    ) -> str:
        mem_id = hashlib.md5(f"{key}:{value}".encode()).hexdigest()[:12]
        self._store[mem_id] = {
            "key": key,
            "value": value,
            "metadata": metadata or {},
            "importance": max(0.0, min(1.0, importance)),
            "created_at": datetime.now().isoformat(),
            "last_accessed": datetime.now().isoformat(),
            "access_count": 0,
        }
        self._enforce_limit()
        return mem_id

    def retrieve(self, query: str, top_k: int = 5) -> List[str]:
        query_lower = query.lower()
        scored = []

        for item in self._store.values():
            text = f"{item['key']} {item['value']}".lower()
            keyword_score = sum(1 for word in query_lower.split() if word in text)
            if keyword_score == 0:
                continue

            # Combined score: keyword + importance + recency/frequency
            freq_boost = min(0.3, item["access_count"] * 0.03)
            score = keyword_score * 1.0 + item["importance"] * 0.8 + freq_boost
            scored.append((score, item))

        scored.sort(key=lambda x: x[0], reverse=True)

        results = []
        for score, item in scored[:top_k]:
            item["access_count"] += 1
            item["last_accessed"] = datetime.now().isoformat()
            results.append(item["value"])

        return results

    def _enforce_limit(self) -> None:
        if len(self._store) <= self.max_items:
            return
        # Ən az vacib + az istifadə olunanları sil
        items = list(self._store.items())
        items.sort(
            key=lambda x: (
                x[1]["importance"] * 0.6 + min(1.0, x[1]["access_count"] * 0.05) * 0.4
            )
        )
        to_remove = len(self._store) - self.max_items
        for mem_id, _ in items[:to_remove]:
            del self._store[mem_id]

    def get_stats(self) -> Dict[str, Any]:
        if not self._store:
            return {"count": 0}
        importances = [v["importance"] for v in self._store.values()]
        return {
            "count": len(self._store),
            "avg_importance": round(sum(importances) / len(importances), 3),
            "max_importance": round(max(importances), 3),
        }

    def clear(self) -> None:
        self._store.clear()
