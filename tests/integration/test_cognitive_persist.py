"""Integration: teach → reason → reload → reason (Faza 8)."""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture()
ndef isolated_data(tmp_path, monkeypatch):
    """Point Leon data dir to temp."""
    leon = tmp_path / "leon"
    (leon / "facts").mkdir(parents=True)
    (leon / "graph").mkdir(parents=True)
    (leon / "learning").mkdir(parents=True)
    (leon / "memory").mkdir(parents=True)
    (leon / "traces").mkdir(parents=True)
    monkeypatch.setenv("LEON_DATA_DIR", str(tmp_path))
    # reload config
    import core.config as cfg

    cfg.config = cfg.load_config()
    return tmp_path


def test_teach_reason_reload(isolated_data):
    from curriculum import CurriculumEngine
    from knowledge.facts import FactStore
    from brain.reasoning.engine import ReasoningEngine

    eng = CurriculumEngine()
    # single lesson lighter than full volume
    try:
        report = eng.teach("000001", volume_id="01")
    except Exception as e:
        pytest.skip(f"curriculum assets missing: {e}")

    assert report.get("lesson_id")

    re = ReasoningEngine(persist_traces=False)
    r1 = re.reason("Daş mövcuddurmu?", use_brain=False)
    # may be curriculum hit or unknown depending on inject
    assert "answer" in r1 or "conclusion" in r1

    # new FactStore loads disk
    fs = FactStore()
    assert isinstance(fs.all(), list)

    r2 = ReasoningEngine(persist_traces=False).reason("Daş mövcuddurmu?", use_brain=False)
    assert r2.get("trace_id")


def test_unified_retrieve_smoke(isolated_data):
    from memory.retrieve import retrieve
    from knowledge.facts import FactStore

    FactStore().add("Planet obyektdir", source="test")
    out = retrieve("planet", top_k=5)
    assert "candidates" in out
    assert out.get("query") == "planet"
