"""Cognitive cycle PODALR smoke."""

from brain.cognitive_cycle import CognitiveCycle


def test_cycle_basic():
    r = CognitiveCycle().run("Daş mövcuddurmu?", learn=True, reflect=True)
    assert r.get("ok")
    assert r.get("cycle_id")
    assert "decision" in r
    phases = [p.get("phase") for p in (r.get("phases") or [])]
    assert "perceive" in phases
    assert "orient" in phases
    assert "decide" in phases
    assert r.get("agi_claim") is False


def test_orient_coding():
    c = CognitiveCycle()
    o = c._orient("python kod yaz", {"ok": True, "modalities": ["text"]}, goal=None)
    assert o.get("task_type") == "coding"
