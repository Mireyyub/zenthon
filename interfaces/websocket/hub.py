"""
WebSocket connection hub + EventBus bridge (Phase 4).

- Clients connect to /ws
- Optional subscribe filter by event name
- Bus events (typed vocabulary) fan-out as JSON
- Client commands: ping, subscribe, unsubscribe, chat, think
"""

from __future__ import annotations

import asyncio
import json
import threading
from typing import Any, Dict, List, Optional, Set

from core.logger import logger

try:
    from core.contracts.events import EventName
except Exception:  # pragma: no cover
    EventName = None  # type: ignore


class ConnectionHub:
    """Manage WS clients and bridge EventBus → async broadcast."""

    def __init__(self) -> None:
        self._clients: Set[Any] = set()  # WebSocket instances
        self._filters: Dict[int, Optional[Set[str]]] = {}  # id(ws) -> allowed names or None=all
        self._lock = threading.Lock()
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._bus_attached = False
        self._queue: Optional[asyncio.Queue] = None

    def set_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        self._loop = loop
        if self._queue is None:
            self._queue = asyncio.Queue(maxsize=500)

    def attach_event_bus(self) -> None:
        if self._bus_attached:
            return
        from core.event_bus import event_bus

        def _on_event(event: Any) -> None:
            payload = event.to_dict() if hasattr(event, "to_dict") else {
                "name": getattr(event, "name", "unknown"),
                "data": getattr(event, "payload", {}),
                "source": getattr(event, "source", "system"),
            }
            self._schedule_broadcast(payload)

        event_bus.subscribe("*", _on_event)
        self._bus_attached = True
        logger.info("[ws-hub] EventBus bridge attached")

    def _schedule_broadcast(self, message: Dict[str, Any]) -> None:
        loop = self._loop
        if loop is None:
            return
        try:
            if loop.is_running():
                asyncio.run_coroutine_threadsafe(self.broadcast(message), loop)
        except Exception as e:
            logger.debug(f"[ws-hub] schedule failed: {e}")

    async def connect(self, websocket: Any) -> None:
        await websocket.accept()
        with self._lock:
            self._clients.add(websocket)
            self._filters[id(websocket)] = None  # all events
        logger.info(f"[ws-hub] connected clients={len(self._clients)}")
        await websocket.send_json(
            {
                "name": "system.started",
                "data": {"message": "Leon WS connected", "protocol": "v1"},
                "source": "websocket",
            }
        )

    def disconnect(self, websocket: Any) -> None:
        with self._lock:
            self._clients.discard(websocket)
            self._filters.pop(id(websocket), None)
        logger.info(f"[ws-hub] disconnected clients={len(self._clients)}")

    def set_filter(self, websocket: Any, names: Optional[List[str]]) -> None:
        with self._lock:
            if names is None:
                self._filters[id(websocket)] = None
            else:
                self._filters[id(websocket)] = set(names)

    async def broadcast(self, message: Dict[str, Any]) -> None:
        name = message.get("name") or ""
        with self._lock:
            targets = list(self._clients)
            filters = dict(self._filters)
        dead = []
        for ws in targets:
            allowed = filters.get(id(ws))
            if allowed is not None and name not in allowed and "*" not in allowed:
                continue
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)

    async def handle_client_message(self, websocket: Any, raw: str) -> None:
        """Parse client JSON or plain text."""
        msg: Dict[str, Any]
        try:
            msg = json.loads(raw)
            if not isinstance(msg, dict):
                msg = {"type": "chat", "text": str(raw)}
        except json.JSONDecodeError:
            msg = {"type": "chat", "text": raw}

        mtype = (msg.get("type") or msg.get("op") or "chat").lower()

        if mtype == "ping":
            await websocket.send_json({"name": "system.health", "data": {"pong": True}, "source": "websocket"})
            return

        if mtype == "subscribe":
            events = msg.get("events") or msg.get("names") or ["*"]
            if events == ["*"] or events == "*":
                self.set_filter(websocket, None)
            else:
                self.set_filter(websocket, [str(e) for e in events])
            await websocket.send_json(
                {"name": "system.health", "data": {"subscribed": events}, "source": "websocket"}
            )
            return

        if mtype == "unsubscribe":
            self.set_filter(websocket, set())  # type: ignore[arg-type]
            with self._lock:
                self._filters[id(websocket)] = set()
            await websocket.send_json(
                {"name": "system.health", "data": {"subscribed": []}, "source": "websocket"}
            )
            return

        if mtype in ("chat", "think", "message"):
            text = msg.get("text") or msg.get("message") or msg.get("query") or ""
            if not text:
                await websocket.send_json(
                    {"name": "system.error", "data": {"error": "empty message"}, "source": "websocket"}
                )
                return
            await self._run_think(websocket, str(text), msg)
            return

        await websocket.send_json(
            {
                "name": "system.error",
                "data": {"error": f"unknown type: {mtype}", "hint": "ping|subscribe|chat|think"},
                "source": "websocket",
            }
        )

    async def _run_think(self, websocket: Any, text: str, msg: Dict[str, Any]) -> None:
        from core.event_bus import event_bus

        corr = msg.get("correlation_id") or msg.get("id")
        event_bus.publish_typed(
            EventName.USER_MESSAGE if EventName else "user.message",
            {"text": text[:2000]},
            source="websocket",
            correlation_id=str(corr) if corr else None,
        )
        event_bus.publish_typed(
            EventName.REASON_STARTED if EventName else "reason.started",
            {"query": text[:500]},
            source="websocket",
            correlation_id=str(corr) if corr else None,
        )

        try:
            from brain.orchestrator import BrainOrchestrator
            from core.config import config

            orch = BrainOrchestrator(brain_name=getattr(config, "ai_name", "Leon") or "Leon")
            result = await asyncio.to_thread(
                orch.run,
                text,
                goal=msg.get("goal"),
                reasoning_mode=msg.get("mode") or "auto",
                agent_type=msg.get("agent"),
            )
            answer = result.get("answer") or result.get("conclusion") or ""
            out = {
                "name": "assistant.message",
                "data": {
                    "answer": answer,
                    "confidence": result.get("confidence"),
                    "source": result.get("source"),
                    "trace_id": result.get("trace_id"),
                    "llm_used": result.get("llm_used"),
                },
                "source": "websocket",
                "correlation_id": corr,
            }
            event_bus.publish_typed(
                EventName.REASON_COMPLETED if EventName else "reason.completed",
                {"answer": str(answer)[:500], "trace_id": result.get("trace_id")},
                source="websocket",
                correlation_id=str(corr) if corr else None,
            )
            event_bus.publish_typed(
                EventName.ASSISTANT_MESSAGE if EventName else "assistant.message",
                {"answer": str(answer)[:500]},
                source="websocket",
                correlation_id=str(corr) if corr else None,
            )
            await websocket.send_json(out)
        except Exception as e:
            logger.error(f"[ws-hub] think failed: {e}")
            event_bus.publish_typed(
                EventName.SYSTEM_ERROR if EventName else "system.error",
                {"error": str(e)},
                source="websocket",
            )
            await websocket.send_json(
                {"name": "system.error", "data": {"error": str(e)}, "source": "websocket"}
            )


ws_hub = ConnectionHub()
