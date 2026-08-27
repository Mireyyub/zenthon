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
    """Thread-safe event bus with a bounded, safe projection for local clients."""

    def __init__(self, max_history: Optional[int] = None, read_model: Optional[Any] = None):
        from core.event_store import EventReadModel

        self._handlers: Dict[str, List[Handler]] = defaultdict(list)
        self._lock = threading.RLock()
        self._history: List[Event] = []
        self._read_model = read_model or EventReadModel.from_config()
        self._max_history = max_history or self._read_model.max_records

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

        try:
            self._read_model.record(event)
        except Exception as e:
            # Observability must not make a successful cognitive operation fail.
            logger.warning(f"EventBus read model write failed: {e}")

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

    def get_public_feed(self, limit: int = 50, after_event_id: Optional[str] = None) -> Dict[str, Any]:
        """Return the sanitized operational projection for GUI/API consumers."""
        return self._read_model.feed(limit=limit, after_event_id=after_event_id)

    def reconfigure_read_model(self) -> None:
        """Apply a completed local desktop profile without restarting the process."""
        from core.event_store import EventReadModel

        with self._lock:
            self._read_model = EventReadModel.from_config()
            self._max_history = self._read_model.max_records

    def clear(self) -> None:
        with self._lock:
            self._handlers.clear()
            self._history.clear()
            self._read_model.clear()


# Global bus
event_bus = EventBus()
