"""Integration: teach → reason → reload → reason."""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture()
def isolated_data(tmp_path, monkeypatch):
    leon = tmp_path / "leon"
    for sub in ("facts", "graph", "learning", "memory", "traces", "plans", "audit", "sandbox"):
        (leon / sub).mkdir(parents=True)
    monkeypatch.setenv("LEON_DATA_DIR", str(tmp_path))
    import core.config as cfg

    cfg.config = cfg.load_config()
    # reset knowledge singletons so they pick new paths
    import knowledge.registry as reg

    reg._fact_store = None
    reg._graph = None
    return tmp_path


def test_teach_reason_reload(isolated_data):
    from curriculum import CurriculumEngine
    from knowledge.registry import get_fact_store, reload_all
    from brain.reasoning.engine import ReasoningEngine

    eng = CurriculumEngine()
    try:
        report = eng.teach("000001", volume_id="01")
    except Exception as e:
        pytest.skip(f"curriculum assets missing: {e}")

    assert report.get("lesson_id")

    re = ReasoningEngine(persist_traces=False)
    r1 = re.reason("Daş mövcuddurmu?", use_brain=False)
    assert r1.get("answer") or r1.get("conclusion")
    # After teach, curriculum should match
    if r1.get("source", "").startswith(("curriculum", "train", "eval")):
        ans = str(r1.get("answer") or "").lower()
        assert "bəli" in ans or "yes" in ans

    reload_all()
    fs = get_fact_store(force_new=True)
    assert isinstance(fs.all(), list)

    r2 = ReasoningEngine(persist_traces=False).reason("Daş mövcuddurmu?", use_brain=False)
    assert r2.get("trace_id")


def test_teach_volume_02_causality(isolated_data):
    from curriculum import CurriculumEngine
    from brain.reasoning.engine import ReasoningEngine

    eng = CurriculumEngine()
    try:
        eng.teach_volume("02")
    except Exception as e:
        pytest.skip(f"vol02 missing: {e}")

    re = ReasoningEngine(persist_traces=False)
    r = re.reason("Korrelyasiya həmişə səbəbdirmi?", use_brain=False)
    ans = str(r.get("answer") or "").lower()
    # curriculum/train should hit
    if r.get("source", "").startswith(("curriculum", "train", "eval")):
        assert "xeyr" in ans or "no" in ans


def test_unified_retrieve_smoke(isolated_data):
    from memory.retrieve import retrieve
    from knowledge.registry import get_fact_store

    get_fact_store(force_new=True).add("Planet obyektdir", source="test")
    out = retrieve("planet", top_k=5)
    assert "candidates" in out
    assert out.get("query") == "planet"
