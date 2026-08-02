"""Fact Store – sadə fakt bazası."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from datetime import datetime
import hashlib


class FactStore:
    def __init__(self):
        self._facts: Dict[str, Dict[str, Any]] = {}

    def add(self, statement: str, source: str = "user", confidence: float = 1.0) -> str:
        fact_id = hashlib.md5(statement.encode()).hexdigest()[:12]
        self._facts[fact_id] = {
            "id": fact_id,
            "statement": statement,
            "source": source,
            "confidence": confidence,
            "created_at": datetime.now().isoformat(),
        }
        return fact_id

    def search(self, query: str, top_k: int = 10) -> List[Dict]:
        q = query.lower()
        scored = []
        for fact in self._facts.values():
            score = sum(1 for w in q.split() if w in fact["statement"].lower())
            if score > 0:
                scored.append((score * fact["confidence"], fact))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [f for _, f in scored[:top_k]]

    def all(self) -> List[Dict]:
        return list(self._facts.values())

    def clear(self) -> None:
        self._facts.clear()
