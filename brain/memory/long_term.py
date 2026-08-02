"""Long-Term Memory"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import hashlib


class LongTermMemory:
    def __init__(self):
        self._store: Dict[str, Dict[str, Any]] = {}

    def store(self, key: str, value: Any, metadata: Optional[Dict] = None) -> str:
        mem_id = hashlib.md5(key.encode()).hexdigest()[:12]
        self._store[mem_id] = {
            "key": key, "value": value, "metadata": metadata or {},
            "created_at": datetime.now().isoformat(), "access_count": 0,
        }
        return mem_id

    def retrieve(self, query: str, top_k: int = 5) -> List[str]:
        query_lower = query.lower()
        scored = []
        for item in self._store.values():
            score = sum(1 for word in query_lower.split() if word in f"{item['key']} {item['value']}".lower())
            if score > 0:
                scored.append((score, item["value"]))
                item["access_count"] += 1
        scored.sort(key=lambda x: x[0], reverse=True)
        return [val for _, val in scored[:top_k]]

    def clear(self) -> None:
        self._store.clear()
