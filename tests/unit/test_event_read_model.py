from __future__ import annotations

from datetime import datetime
from pathlib import Path

import json

import pytest


def test_event_read_model_persists_bounded_redacted_feed(tmp_path: Path):
    from core.event_bus import Event, EventBus
    from core.event_store import EventReadModel

    path = tmp_path / "events.json"
    bus = EventBus(read_model=EventReadModel(path, max_records=10))
    event = bus.publish(
        "ReasoningCompleted",
        {
            "confidence": 0.82,
            "trace_id": "TR-1",
            "query": "private user question",
            "raw_reasoning": "private deliberation",
        },
        source="reasoning",
    )

    feed = bus.get_public_feed()
    assert feed["count"] == 1
    row = feed["events"][0]
    assert row["event_id"] == event.event_id
    assert row["data"] == {"confidence": 0.82, "trace_id": "TR-1"}
    assert row["redacted_field_count"] == 2

    restarted = EventReadModel(path, max_records=10)
    assert restarted.feed()["events"][0]["event_id"] == event.event_id


def test_event_read_model_uses_cursor_and_retention(tmp_path: Path):
    from core.event_bus import Event
    from core.event_store import EventReadModel

    store = EventReadModel(tmp_path / "events.json", max_records=10, persist=False)
    first = Event(name="SystemStarted", event_id="first", timestamp=datetime(2026, 1, 1))
    second = Event(name="TaskCompleted", event_id="second", timestamp=datetime(2026, 1, 1))
    store.record(first)
    store.record(second)

    feed = store.feed(after_event_id="first")
    assert [row["event_id"] for row in feed["events"]] == ["second"]


def test_event_read_model_redacts_untrusted_persisted_data(tmp_path: Path):
    from core.event_store import EventReadModel

    path = tmp_path / "events.json"
    path.write_text(
        json.dumps(
            [
                {
                    "event_id": "persisted",
                    "name": "ReasoningCompleted",
                    "source": "reasoning",
                    "timestamp": "2026-01-01T00:00:00Z",
                    "severity": "info",
                    "summary": "reasoning: ReasoningCompleted",
                    "data": {"confidence": 0.5, "raw_reasoning": "must remain private"},
                }
            ]
        ),
        encoding="utf-8",
    )

    row = EventReadModel(path).feed()["events"][0]
    assert row["data"] == {"confidence": 0.5}
    assert row["redacted_field_count"] == 1


def test_native_event_feed_rejects_non_loopback_client():
    from fastapi import HTTPException
    from interfaces.api.main import _require_loopback

    class Client:
        host = "192.0.2.20"

    class FakeRequest:
        client = Client()

    with pytest.raises(HTTPException) as exc:
        _require_loopback(FakeRequest())
    assert exc.value.status_code == 403


def test_native_event_feed_returns_redacted_http_projection():
    from fastapi.testclient import TestClient
    from core.event_bus import event_bus
    from interfaces.api.main import app

    event_bus.clear()
    try:
        event_bus.publish(
            "TaskCompleted",
            {"task_id": "task-1", "success": True, "result": "private result"},
            source="scheduler",
        )
        response = TestClient(app).get("/native-core/events")
        assert response.status_code == 200
        row = response.json()["events"][-1]
        assert row["data"] == {"task_id": "task-1", "success": True}
        assert row["redacted_field_count"] == 1
    finally:
        event_bus.clear()
