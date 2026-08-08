"""SelfView body awareness tests."""

from brain.self_view import SelfView
from brain.policy_bind import bind_mutate_policy


def test_policy_bind():
    assert bind_mutate_policy() is True


def test_body_map():
    b = SelfView().body()
    assert b.get("identity") == "Leon"
    assert "summary" in b
    assert "cells" in b
    assert b["summary"].get("python_modules", 0) > 10


def test_read_engine():
    r = SelfView().read("brain/reasoning/engine.py", start=1, max_lines=20)
    assert r.get("ok")
    assert r.get("total_lines", 0) > 20
    assert len(r.get("lines") or []) > 0


def test_symbols_orchestrator():
    s = SelfView().symbols("brain/orchestrator.py")
    assert s.get("ok")
    # has classes or functions
    assert (s.get("classes") or s.get("functions"))


def test_search_reasoning():
    h = SelfView().search("ReasoningEngine", max_hits=5)
    assert h.get("ok")
    assert len(h.get("hits") or []) >= 1


def test_security_not_mutable():
    m = SelfView().mutability("security/gate.py")
    assert m.get("mutable") is False
