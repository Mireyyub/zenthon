"""
Async Event Bus – asyncio uyğun event sistemi.

Sinxron EventBus ilə paralel yaşayır; ağır işlərdə async publish/subscribe.
"""

from __future__ import annotations

import asyncio
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Awaitable, Callable, Dict, List, Optional
import uuid

from core.logger import logger


@dataclass
class AsyncEvent:
    name: str
    payload: Dict[str, Any] = field(default_factory=dict)
    source: str = "system"
    event_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    timestamp: datetime = field(default_factory=datetime.now)


AsyncHandler = Callable[[AsyncEvent], Awaitable[None]]


class AsyncEventBus:
    def __init__(self):
        self._handlers: Dict[str, List[AsyncHandler]] = defaultdict(list)
        self._history: List[AsyncEvent] = []
        self._max_history = 500
        self._lock = asyncio.Lock()

    def subscribe(self, event_name: str, handler: AsyncHandler) -> None:
        if handler not in self._handlers[event_name]:
            self._handlers[event_name].append(handler)
            logger.debug(f"AsyncEventBus: subscribed '{event_name}'")

    def unsubscribe(self, event_name: str, handler: AsyncHandler) -> None:
        if handler in self._handlers[event_name]:
            self._handlers[event_name].remove(handler)

    async def publish(
        self,
        event_name: str,
        payload: Optional[Dict[str, Any]] = None,
        source: str = "system",
    ) -> AsyncEvent:
        event = AsyncEvent(name=event_name, payload=payload or {}, source=source)
        async with self._lock:
            self._history.append(event)
            if len(self._history) > self._max_history:
                self._history = self._history[-self._max_history :]
            handlers = list(self._handlers.get(event_name, []))
            handlers += list(self._handlers.get("*", []))

        if handlers:
            results = await asyncio.gather(
                *[self._safe_call(h, event) for h in handlers],
                return_exceptions=True,
            )
            for r in results:
                if isinstance(r, Exception):
                    logger.error(f"AsyncEventBus handler error on '{event_name}': {r}")

        return event

    async def _safe_call(self, handler: AsyncHandler, event: AsyncEvent) -> None:
        await handler(event)

    def get_history(self, event_name: Optional[str] = None, limit: int = 50) -> List[AsyncEvent]:
        items = self._history
        if event_name:
            items = [e for e in items if e.name == event_name]
        return items[-limit:]


async_event_bus = AsyncEventBus()
