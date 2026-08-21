"""Unit: FactStore, KnowledgeGraph integrity, LearningEngine (Faza 8)."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest


@pytest.fixture()
def tmp_paths(tmp_path: Path):
    return {
        "facts": tmp_path / "facts.json",
        "graph": tmp_path / "graph.json",
        "learning": tmp_path / "records.json",
    }


def test_fact_store_persist_roundtrip(tmp_paths):
    from knowledge.facts import FactStore

    fs = FactStore(path=tmp_paths["facts"], auto_persist=True)
    fid = fs.add("Alma obyektdir", source="test", confidence=0.9)
    assert fid
    assert any("Alma" in f["statement"] for f in fs.all())

    fs2 = FactStore(path=tmp_paths["facts"], auto_persist=True)
    assert len(fs2.all()) >= 1
    hits = fs2.search("Alma")
    assert hits


def test_graph_integrity_and_is_a(tmp_paths):
    from knowledge.graph import KnowledgeGraph

    kg = KnowledgeGraph(path=tmp_paths["graph"], auto_persist=True)
    a = kg.add_node("alma", node_type="entity")
    o = kg.add_node("Obyekt", node_type="concept")
    kg.add_edge(a, o, "is_a")
    stats = kg.stats()
    assert stats["nodes"] >= 2
    assert stats["edges"] >= 1
    integrity = kg.validate_integrity()
    assert integrity["ok"] is True

    kg2 = KnowledgeGraph(path=tmp_paths["graph"], auto_persist=True)
    assert kg2.stats()["nodes"] >= 2


def test_learning_engine_validate_and_quarantine(tmp_paths):
    from learning.engine import LearningEngine

    eng = LearningEngine(path=tmp_paths["learning"], auto_persist=True)
    weak = eng.observe("zəif iddia test", source="test", confidence=0.4)
    assert weak.status in ("pending", "rejected")
    strong = eng.observe("Güclü fakt: daş varlıqdır", source="test", confidence=0.95)
    assert strong.status == "validated"
    st = eng.stats()
    assert st["records"] >= 1


def test_composite_confidence():
    from brain.confidence import composite_confidence, action_from_confidence

    pack = composite_confidence(
        base=0.8,
        evidence_quality=0.9,
        source_reliability=0.9,
        consistency=0.9,
        method="curriculum",
    )
    assert 0.0 <= pack["score"] <= 1.0
    act = action_from_confidence(pack["score"])
    assert "action" in act
