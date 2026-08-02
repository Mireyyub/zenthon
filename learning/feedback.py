"""Feedback Collector – istifadəçi və sistem geribildirimi."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from datetime import datetime
import uuid

from core.event_bus import event_bus


class FeedbackCollector:
    def __init__(self):
        self._feedback: List[Dict[str, Any]] = []

    def add(
        self,
        content: str,
        score: float = 0.0,
        source: str = "user",
        context: Optional[Dict] = None,
    ) -> str:
        fb_id = str(uuid.uuid4())[:10]
        entry = {
            "id": fb_id,
            "content": content,
            "score": max(-1.0, min(1.0, score)),
            "source": source,
            "context": context or {},
            "timestamp": datetime.now().isoformat(),
        }
        self._feedback.append(entry)
        event_bus.publish("FeedbackReceived", {"id": fb_id, "score": score}, source="learning")
        return fb_id

    def recent(self, n: int = 20) -> List[Dict]:
        return self._feedback[-n:]

    def average_score(self) -> float:
        if not self._feedback:
            return 0.0
        return sum(f["score"] for f in self._feedback) / len(self._feedback)

    def clear(self) -> None:
        self._feedback.clear()
