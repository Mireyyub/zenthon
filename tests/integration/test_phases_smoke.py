"""Integration smoke for phases 1–8."""

from __future__ import annotations


def test_fact_singleton_persist():
    from knowledge.registry import get_fact_store

    fs = get_fact_store(force_new=True)
    marker = "PHASE_SMOKE_MARKER_XYZ"
    fs.add(marker, source="test")
    fs2 = get_fact_store(force_new=True)
    assert any(marker in f.get("statement", "") for f in fs2.all())


def test_reasoning_has_trace():
    from brain.reasoning.engine import ReasoningEngine

    r = ReasoningEngine(persist_traces=False).reason("test sual", use_brain=False)
    assert r.get("trace_id")
    assert "confidence" in r


def test_omniverse_stub():
    from integrations.omniverse import OmniverseBridge

    ov = OmniverseBridge()
    ov.load_stub_demo_scene()
    assert ov.status()["objects"] >= 1
