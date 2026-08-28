"""
Event Bus – modullar arası zəif bağlı kommunikasiya.

Phase 4: accepts EventName enum + publish_typed; wire format via Event.to_dict().
Legacy publish(str, payload) unchanged.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Union
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
import threading
import uuid

from core.logger import logger

try:
    from core.contracts.events import EventName, EventPayload, make_event_payload
except Exception:  # pragma: no cover
    EventName = None  # type: ignore
    EventPayload = None  # type: ignore
    make_event_payload = None  # type: ignore


@dataclass
class Event:
    name: str
    payload: Dict[str, Any] = field(default_factory=dict)
    source: str = "system"
    event_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    timestamp: datetime = field(default_factory=datetime.now)
    correlation_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        ts = self.timestamp
        if isinstance(ts, datetime):
            ts_s = ts.isoformat()
        else:
            ts_s = str(ts)
        return {
            "name": self.name,
            "data": self.payload,
            "source": self.source,
            "event_id": self.event_id,
            "timestamp": ts_s,
            "correlation_id": self.correlation_id,
        }


Handler = Callable[[Event], None]
EventNameLike = Union[str, Any]  # str | EventName


def _normalize_name(event_name: EventNameLike) -> str:
    if EventName is not None and isinstance(event_name, EventName):
        return event_name.value
    if hasattr(event_name, "value") and isinstance(getattr(event_name, "value"), str):
        return str(event_name.value)
    return str(event_name)


class EventBus:
    """Thread-safe in-process event bus."""

    def __init__(self):
        self._handlers: Dict[str, List[Handler]] = defaultdict(list)
        self._lock = threading.RLock()
        self._history: List[Event] = []
        self._max_history = 500

    def subscribe(self, event_name: EventNameLike, handler: Handler) -> None:
        name = _normalize_name(event_name)
        with self._lock:
            if handler not in self._handlers[name]:
                self._handlers[name].append(handler)
                logger.debug(f"EventBus: subscribed to '{name}'")

    def unsubscribe(self, event_name: EventNameLike, handler: Handler) -> None:
        name = _normalize_name(event_name)
        with self._lock:
            if handler in self._handlers[name]:
                self._handlers[name].remove(handler)

    def publish(
        self,
        event_name: EventNameLike,
        payload: Optional[Dict[str, Any]] = None,
        source: str = "system",
        *,
        correlation_id: Optional[str] = None,
    ) -> Event:
        name = _normalize_name(event_name)
        event = Event(
            name=name,
            payload=payload or {},
            source=source,
            correlation_id=correlation_id,
        )
        with self._lock:
            self._history.append(event)
            if len(self._history) > self._max_history:
                self._history = self._history[-self._max_history :]
            handlers = list(self._handlers.get(name, []))
            handlers += list(self._handlers.get("*", []))

        for h in handlers:
            try:
                h(event)
            except Exception as e:
                logger.error(f"EventBus handler error on '{name}': {e}")

        logger.debug(f"EventBus: published '{name}' from {source}")
        return event

    def publish_typed(
        self,
        name: EventNameLike,
        data: Optional[Dict[str, Any]] = None,
        *,
        source: str = "system",
        correlation_id: Optional[str] = None,
    ) -> Event:
        """Publish using EventName vocabulary; same runtime path as publish()."""
        if make_event_payload is not None:
            env = make_event_payload(
                name, data, source=source, correlation_id=correlation_id
            )
            return self.publish(
                env.name,
                env.data,
                source=env.source,
                correlation_id=env.correlation_id,
            )
        return self.publish(name, data, source=source, correlation_id=correlation_id)

    def get_history(
        self, event_name: Optional[EventNameLike] = None, limit: int = 50
    ) -> List[Event]:
        with self._lock:
            items = self._history
            if event_name is not None:
                n = _normalize_name(event_name)
                items = [e for e in items if e.name == n]
            return items[-limit:]

    def clear(self) -> None:
        with self._lock:
            self._handlers.clear()
            self._history.clear()


# Global bus
event_bus = EventBus()
