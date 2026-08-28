"""WebSocket interface — typed events (Phase 4)."""

from interfaces.websocket.server import create_ws_app, register_websocket
from interfaces.websocket.hub import ws_hub

__all__ = ["create_ws_app", "register_websocket", "ws_hub"]
