"""Semantic Memory – faktlar, anlayışlar, əlaqələr."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Set
from datetime import datetime
import hashlib


class SemanticMemory:
    """Açar-dəyər + sadə əlaqə qrafı."""

    def __init__(self):
        self._facts: Dict[str, Dict[str, Any]] = {}
        self._relations: Dict[str, Set[str]] = {}  # fact_id → related fact_ids

    def store_fact(self, subject: str, predicate: str, obj: str, confidence: float = 1.0) -> str:
        key = f"{subject}|{predicate}|{obj}"
        fact_id = hashlib.md5(key.encode()).hexdigest()[:12]
        self._facts[fact_id] = {
            "id": fact_id,
            "subject": subject,
            "predicate": predicate,
            "object": obj,
            "confidence": confidence,
            "created_at": datetime.now().isoformat(),
        }
        return fact_id

    def relate(self, fact_id_a: str, fact_id_b: str) -> None:
        self._relations.setdefault(fact_id_a, set()).add(fact_id_b)
        self._relations.setdefault(fact_id_b, set()).add(fact_id_a)

    def query(self, subject: Optional[str] = None, predicate: Optional[str] = None) -> List[Dict]:
        results = []
        for fact in self._facts.values():
            if subject and subject.lower() not in fact["subject"].lower():
                continue
            if predicate and predicate.lower() not in fact["predicate"].lower():
                continue
            results.append(fact)
        return results

    def get_related(self, fact_id: str) -> List[Dict]:
        related_ids = self._relations.get(fact_id, set())
        return [self._facts[fid] for fid in related_ids if fid in self._facts]

    def all_facts(self) -> List[Dict]:
        return list(self._facts.values())

    def clear(self) -> None:
        self._facts.clear()
        self._relations.clear()
