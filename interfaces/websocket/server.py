"""
WebSocket server — Phase 4 typed events.

Preferred path: mount on main FastAPI app via register_websocket(app).
Standalone create_ws_app() kept for optional separate process.
"""
from __future__ import annotations

from typing import Any, Optional

from core.logger import logger


def register_websocket(app: Any) -> None:
    """Attach /ws to an existing FastAPI application."""
    try:
        from fastapi import WebSocket, WebSocketDisconnect
    except ImportError:
        logger.warning("[websocket] fastapi not available — skip /ws")
        return

    from interfaces.websocket.hub import ws_hub

    @app.on_event("startup")
    async def _ws_startup() -> None:
        import asyncio

        ws_hub.set_loop(asyncio.get_running_loop())
        ws_hub.attach_event_bus()

    @app.websocket("/ws")
    async def ws_endpoint(websocket: WebSocket) -> None:
        await ws_hub.connect(websocket)
        try:
            while True:
                data = await websocket.receive_text()
                await ws_hub.handle_client_message(websocket, data)
        except WebSocketDisconnect:
            ws_hub.disconnect(websocket)
        except Exception as e:
            logger.error(f"[websocket] error: {e}")
            ws_hub.disconnect(websocket)

    logger.info("[websocket] /ws registered on main app")


def create_ws_app():
    """Standalone FastAPI app with only /ws (legacy helper)."""
    try:
        from fastapi import FastAPI
    except ImportError:
        logger.warning("[websocket] fastapi not available")
        return None

    app = FastAPI(title="Leon WebSocket", version="0.7.0")
    register_websocket(app)
    return app
