"""Atomic persist + research agent smoke."""

from __future__ import annotations

from pathlib import Path


def test_atomic_write_json(tmp_path: Path):
    from core.persistence import write_json, read_json

    p = tmp_path / "t.json"
    write_json(p, {"ok": True, "n": 1})
    assert read_json(p)["ok"] is True


def test_research_agent_no_crash():
    from agents.manager import agent_manager

    a = agent_manager.create("research", allow_experimental=True)
    r = agent_manager.run(a.id, "Daş mövcuddurmu?")
    # may succeed via curriculum/retrieve or fail if empty – must not raise
    assert r is not None
    assert hasattr(r, "success")


def test_vision_stub_honest():
    from agents.manager import agent_manager

    a = agent_manager.create("vision", allow_experimental=True)
    r = agent_manager.run(a.id, "what is in the image?")
    assert r.success is False
    assert "not implemented" in (r.error or "").lower()
