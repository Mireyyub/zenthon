"""
WebSocket server — zenthon_v10 adapted.
Soft-fails if fastapi WS not available.
"""
from __future__ import annotations

from typing import Any, Dict

from core.logger import logger


def create_ws_app():
    """Return FastAPI app with /ws endpoint if possible, else None."""
    try:
        from fastapi import FastAPI, WebSocket, WebSocketDisconnect
    except ImportError:
        logger.warning("[websocket] fastapi not available")
        return None

    app = FastAPI(title="Leon WebSocket")

    @app.websocket("/ws")
    async def ws_endpoint(websocket: WebSocket):
        await websocket.accept()
        logger.info("[websocket] client connected")
        try:
            while True:
                data = await websocket.receive_text()
                reply: Dict[str, Any] = {"type": "echo", "text": data}
                try:
                    from brain.orchestrator import Orchestrator
                    orch = Orchestrator()
                    if hasattr(orch, "think"):
                        result = orch.think(data)
                        reply = {"type": "think", "result": str(result)[:2000]}
                except Exception as e:
                    reply["note"] = f"think unavailable: {e}"
                await websocket.send_json(reply)
        except WebSocketDisconnect:
            logger.info("[websocket] client disconnected")
        except Exception as e:
            logger.error(f"[websocket] error: {e}")

    return app
