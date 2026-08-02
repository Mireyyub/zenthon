"""
Event Bus – modullar arası zəif bağlı kommunikasiya.

Nümunə eventlər:
  UserMessageReceived, MemoryUpdated, TaskCompleted,
  AgentCreated, ModelResponseGenerated, LearningFinished
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
import threading
import uuid

from core.logger import logger


@dataclass
class Event:
    name: str
    payload: Dict[str, Any] = field(default_factory=dict)
    source: str = "system"
    event_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    timestamp: datetime = field(default_factory=datetime.now)


Handler = Callable[[Event], None]


class EventBus:
    """Thread-safe in-process event bus."""

    def __init__(self):
        self._handlers: Dict[str, List[Handler]] = defaultdict(list)
        self._lock = threading.RLock()
        self._history: List[Event] = []
        self._max_history = 500

    def subscribe(self, event_name: str, handler: Handler) -> None:
        with self._lock:
            if handler not in self._handlers[event_name]:
                self._handlers[event_name].append(handler)
                logger.debug(f"EventBus: subscribed to '{event_name}'")

    def unsubscribe(self, event_name: str, handler: Handler) -> None:
        with self._lock:
            if handler in self._handlers[event_name]:
                self._handlers[event_name].remove(handler)

    def publish(
        self,
        event_name: str,
        payload: Optional[Dict[str, Any]] = None,
        source: str = "system",
    ) -> Event:
        event = Event(name=event_name, payload=payload or {}, source=source)
        with self._lock:
            self._history.append(event)
            if len(self._history) > self._max_history:
                self._history = self._history[-self._max_history :]
            handlers = list(self._handlers.get(event_name, []))
            # wildcard listeners
            handlers += list(self._handlers.get("*", []))

        for h in handlers:
            try:
                h(event)
            except Exception as e:
                logger.error(f"EventBus handler error on '{event_name}': {e}")

        logger.debug(f"EventBus: published '{event_name}' from {source}")
        return event

    def get_history(self, event_name: Optional[str] = None, limit: int = 50) -> List[Event]:
        with self._lock:
            items = self._history
            if event_name:
                items = [e for e in items if e.name == event_name]
            return items[-limit:]

    def clear(self) -> None:
        with self._lock:
            self._handlers.clear()
            self._history.clear()


# Global bus
event_bus = EventBus()
