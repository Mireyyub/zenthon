"""Phase 4 — typed events + WebSocket hub."""

from __future__ import annotations


def test_event_bus_accepts_event_name_enum():
    from core.event_bus import EventBus
    from core.contracts.events import EventName

    bus = EventBus()
    seen = []

    def handler(ev):
        seen.append(ev.name)

    bus.subscribe(EventName.USER_MESSAGE, handler)
    bus.publish_typed(EventName.USER_MESSAGE, {"text": "hi"}, source="test")
    assert "user.message" in seen
    hist = bus.get_history(EventName.USER_MESSAGE)
    assert len(hist) >= 1
    assert hist[-1].to_dict()["name"] == "user.message"


def test_event_to_dict_wire_format():
    from core.event_bus import Event

    e = Event(name="reason.completed", payload={"x": 1}, source="unit")
    d = e.to_dict()
    assert d["name"] == "reason.completed"
    assert d["data"]["x"] == 1
    assert "event_id" in d and "timestamp" in d


def test_legacy_string_publish_still_works():
    from core.event_bus import EventBus

    bus = EventBus()
    seen = []
    bus.subscribe("AgentStarted", lambda e: seen.append(e.name))
    bus.publish("AgentStarted", {"id": "1"})
    assert seen == ["AgentStarted"]


def test_ws_registered_on_main_app():
    from interfaces.api.main import app

    paths = []
    for r in app.routes:
        p = getattr(r, "path", None)
        if p:
            paths.append(p)
    assert "/ws" in paths or any("ws" in (p or "") for p in paths)


def test_hub_filter_and_disconnect():
    from interfaces.websocket.hub import ConnectionHub

    hub = ConnectionHub()

    class FakeWS:
        def __init__(self):
            self.sent = []

        async def accept(self):
            return None

        async def send_json(self, msg):
            self.sent.append(msg)

    import asyncio

    async def _run():
        ws = FakeWS()
        await hub.connect(ws)
        hub.set_filter(ws, ["user.message"])
        await hub.broadcast({"name": "user.message", "data": {"a": 1}})
        await hub.broadcast({"name": "other.event", "data": {}})
        assert any(m.get("name") == "user.message" for m in ws.sent)
        # other.event should be filtered (except system.started on connect)
        assert not any(m.get("name") == "other.event" for m in ws.sent)
        hub.disconnect(ws)

    asyncio.get_event_loop().run_until_complete(_run())


def test_root_mentions_websocket():
    try:
        from fastapi.testclient import TestClient
    except Exception:
        return
    from interfaces.api.main import app

    client = TestClient(app)
    r = client.get("/")
    assert r.status_code == 200
    assert r.json().get("websocket") == "/ws"
