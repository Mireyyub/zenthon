"""Fact Store – diskə yazılan fakt bazası (Faza 1)."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from datetime import datetime
from pathlib import Path
import hashlib

from core.persistence import write_json, read_json


class FactStore:
    def __init__(self, path: Optional[Path | str] = None, auto_persist: bool = True):
        if path is None:
            try:
                from core.config import config

                path = config.path.facts_dir / "facts.json"
            except Exception:
                path = Path("data/leon/facts/facts.json")
        self.path = Path(path)
        self.auto_persist = auto_persist
        self._facts: Dict[str, Dict[str, Any]] = {}
        self.load()

    def add(self, statement: str, source: str = "user", confidence: float = 1.0) -> str:
        fact_id = hashlib.md5(statement.encode()).hexdigest()[:12]
        self._facts[fact_id] = {
            "id": fact_id,
            "statement": statement,
            "source": source,
            "confidence": confidence,
            "created_at": datetime.now().isoformat(),
        }
        if self.auto_persist:
            self.save()
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
        if self.auto_persist:
            self.save()

    def save(self) -> None:
        write_json(self.path, {"facts": self._facts})

    def load(self) -> int:
        data = read_json(self.path, default={})
        if not data:
            return 0
        facts = data.get("facts") if isinstance(data, dict) else None
        if isinstance(facts, dict):
            self._facts = facts
        elif isinstance(data, dict) and data and "statement" in next(iter(data.values()), {}):
            self._facts = data
        return len(self._facts)
