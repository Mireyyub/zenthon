"""Working Memory – capacity + TTL (Faza 4)."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from collections import OrderedDict
from datetime import datetime, timedelta
import uuid


class WorkingMemory:
    """Məhdud tutumlu, TTL ilə iş yaddaşı."""

    def __init__(self, capacity: int = 32, ttl_seconds: int = 1800):
        self.capacity = capacity
        self.ttl_seconds = ttl_seconds
        self._items: OrderedDict[str, Dict[str, Any]] = OrderedDict()

    def _purge_expired(self) -> int:
        if self.ttl_seconds <= 0:
            return 0
        now = datetime.now()
        dead = []
        for k, v in self._items.items():
            try:
                ts = datetime.fromisoformat(v["timestamp"])
                if (now - ts).total_seconds() > self.ttl_seconds:
                    dead.append(k)
            except Exception:
                continue
        for k in dead:
            self._items.pop(k, None)
        return len(dead)

    def add(self, content: Any, tag: str = "general", importance: float = 0.5) -> str:
        self._purge_expired()
        item_id = str(uuid.uuid4())[:8]
        self._items[item_id] = {
            "id": item_id,
            "content": content,
            "tag": tag,
            "importance": max(0.0, min(1.0, importance)),
            "timestamp": datetime.now().isoformat(),
            "ttl_seconds": self.ttl_seconds,
        }
        while len(self._items) > self.capacity:
            sorted_ids = sorted(
                self._items.keys(),
                key=lambda k: self._items[k]["importance"],
            )
            self._items.pop(sorted_ids[0])
        return item_id

    def get(self, item_id: str) -> Optional[Dict]:
        self._purge_expired()
        return self._items.get(item_id)

    def get_by_tag(self, tag: str) -> List[Dict]:
        self._purge_expired()
        return [v for v in self._items.values() if v["tag"] == tag]

    def all(self) -> List[Dict]:
        self._purge_expired()
        return list(self._items.values())

    def clear(self) -> None:
        self._items.clear()

    def stats(self) -> Dict[str, Any]:
        self._purge_expired()
        return {
            "count": len(self._items),
            "capacity": self.capacity,
            "ttl_seconds": self.ttl_seconds,
        }

    def __len__(self) -> int:
        self._purge_expired()
        return len(self._items)
