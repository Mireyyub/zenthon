"""Working Memory – cari düşüncə prosesi üçün müvəqqəti yaddaş."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from collections import OrderedDict
from datetime import datetime
import uuid


class WorkingMemory:
    """Məhdud tutumlu, diqqət əsaslı iş yaddaşı."""

    def __init__(self, capacity: int = 32):
        self.capacity = capacity
        self._items: OrderedDict[str, Dict[str, Any]] = OrderedDict()

    def add(self, content: Any, tag: str = "general", importance: float = 0.5) -> str:
        item_id = str(uuid.uuid4())[:8]
        self._items[item_id] = {
            "id": item_id,
            "content": content,
            "tag": tag,
            "importance": max(0.0, min(1.0, importance)),
            "timestamp": datetime.now().isoformat(),
        }
        while len(self._items) > self.capacity:
            # ən az vacib + ən köhnəni sil
            sorted_ids = sorted(
                self._items.keys(),
                key=lambda k: self._items[k]["importance"],
            )
            self._items.pop(sorted_ids[0])
        return item_id

    def get(self, item_id: str) -> Optional[Dict]:
        return self._items.get(item_id)

    def get_by_tag(self, tag: str) -> List[Dict]:
        return [v for v in self._items.values() if v["tag"] == tag]

    def all(self) -> List[Dict]:
        return list(self._items.values())

    def clear(self) -> None:
        self._items.clear()

    def __len__(self) -> int:
        return len(self._items)
