"""Phase 3 — /api/v1 gateway surface tests."""

from __future__ import annotations


def test_v1_router_mounted():
    from interfaces.api.main import app

    paths = {getattr(r, "path", None) for r in app.routes}
    assert "/api/v1/health" in paths or any(
        (getattr(r, "path", "") or "").startswith("/api/v1") for r in app.routes
    )


def test_v1_index_and_health_via_testclient():
    try:
        from fastapi.testclient import TestClient
    except Exception:
        return  # optional if starlette test client missing

    from interfaces.api.main import app

    client = TestClient(app)
    r = client.get("/api/v1/")
    assert r.status_code == 200
    data = r.json()
    assert data.get("prefix") == "/api/v1"
    assert "endpoints" in data

    h = client.get("/api/v1/health")
    assert h.status_code == 200
    body = h.json()
    assert "ok" in body or "components" in body


def test_legacy_routes_still_present():
    from interfaces.api.main import app

    paths = {getattr(r, "path", None) for r in app.routes}
    assert "/health" in paths
    assert "/think" in paths
    assert "/reason" in paths


def test_task_store_roundtrip():
    from interfaces.api.v1.tasks_store import TaskStore

    store = TaskStore()
    t = store.create("demo", goal="g", action="reason")
    assert t.id.startswith("TK-")
    got = store.get(t.id)
    assert got is not None
    assert got.title == "demo"
    listed = store.list()
    assert any(x.id == t.id for x in listed)


def test_v1_tasks_http():
    try:
        from fastapi.testclient import TestClient
    except Exception:
        return

    from interfaces.api.main import app

    client = TestClient(app)
    created = client.post(
        "/api/v1/tasks",
        json={"title": "phase3-test", "goal": "check", "action": "reason"},
    )
    assert created.status_code == 200
    tid = created.json()["task"]["id"]
    got = client.get(f"/api/v1/tasks/{tid}")
    assert got.status_code == 200
    assert got.json()["task"]["title"] == "phase3-test"
    listed = client.get("/api/v1/tasks")
    assert listed.status_code == 200
    assert listed.json()["durable"] is False


def test_v1_models_endpoint():
    try:
        from fastapi.testclient import TestClient
    except Exception:
        return

    from interfaces.api.main import app

    client = TestClient(app)
    r = client.get("/api/v1/models")
    assert r.status_code == 200
    data = r.json()
    assert "provider" in data
    assert "reachable" in data
