"""Short-Term (Working) Memory"""

from collections import deque
from typing import List, Any
from datetime import datetime


class ShortTermMemory:
    def __init__(self, capacity: int = 20):
        self.capacity = capacity
        self._buffer: deque = deque(maxlen=capacity)

    def add(self, item: Any) -> None:
        self._buffer.append({"content": str(item), "timestamp": datetime.now().isoformat()})

    def retrieve(self, top_k: int = 5) -> List[str]:
        items = list(self._buffer)[-top_k:]
        return [it["content"] for it in reversed(items)]

    def clear(self) -> None:
        self._buffer.clear()

    def __len__(self) -> int:
        return len(self._buffer)
