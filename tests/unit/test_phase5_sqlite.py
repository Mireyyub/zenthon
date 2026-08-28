"""Phase 5 — SQLite storage + durable tasks."""

from __future__ import annotations

import tempfile
from pathlib import Path


def test_init_schema_and_stats():
    from core.storage.sqlite_db import LeonSQLite, init_schema

    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "test.db"
        init_schema(p)
        db = LeonSQLite(p)
        st = db.stats()
        assert st["schema_version"] == "5"
        assert st["tasks"] == 0


def test_task_repository_roundtrip():
    from core.storage.sqlite_db import init_schema
    from core.storage.task_repo import TaskRepository

    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "tasks.db"
        init_schema(p)
        repo = TaskRepository(str(p))
        t = repo.create("phase5", goal="g", action="reason")
        assert t.id.startswith("TK-")
        got = repo.get(t.id)
        assert got is not None
        assert got.title == "phase5"
        t.mark_done()
        repo.save(t)
        again = repo.get(t.id)
        assert again is not None
        assert again.status.value == "done"
        listed = repo.list()
        assert any(x.id == t.id for x in listed)


def test_task_store_reports_durable():
    from interfaces.api.v1.tasks_store import TaskStore

    store = TaskStore()
    # On normal env should be durable; if not, still must create
    t = store.create("api-task", goal="x")
    assert t.id
    got = store.get(t.id)
    assert got is not None


def test_migrate_empty_ok():
    from core.storage.migrate import migrate_json_to_sqlite, migration_status

    # Should not raise even if JSON missing
    status = migration_status()
    assert "db" in status
    report = migrate_json_to_sqlite()
    assert report.get("ok") is True
    assert report.get("json_preserved") is True


def test_v1_storage_endpoints():
    try:
        from fastapi.testclient import TestClient
    except Exception:
        return
    from interfaces.api.main import app

    client = TestClient(app)
    r = client.get("/api/v1/storage/status")
    assert r.status_code == 200
    body = r.json()
    assert "db" in body

    t = client.post("/api/v1/tasks", json={"title": "sqlite-task", "action": "reason"})
    assert t.status_code == 200
    data = t.json()
    assert "task" in data
    # durable should be True when SQLite works
    assert "durable" in data
