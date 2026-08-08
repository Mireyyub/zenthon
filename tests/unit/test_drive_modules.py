"""Smoke tests for Drive-integrated modules."""
from __future__ import annotations

import pytest


def test_decision_engine_basic():
    from agents.decision_engine import DecisionEngine
    eng = DecisionEngine()
    result = eng.decide(
        [
            {"id": "a", "description": "fast", "scores": {"accuracy": 0.6, "latency": 0.9, "compute": 0.8, "reliability": 0.7, "complexity": 0.8}},
            {"id": "b", "description": "accurate", "scores": {"accuracy": 0.95, "latency": 0.4, "compute": 0.5, "reliability": 0.9, "complexity": 0.4}},
        ],
        task_type="critical",
    )
    assert result.winner.id in ("a", "b")
    assert result.margin >= 0
    assert "Seçilən" in result.report()


def test_dag_runner_sync():
    from brain.planning.dag_runner import DAGRunner, DAGNode

    def step1(dep_results=None):
        return "ok1"

    def step2(dep_results=None):
        assert dep_results and "t1" in dep_results
        return "ok2"

    nodes = [
        DAGNode(id="t1", label="one", func=step1),
        DAGNode(id="t2", label="two", func=step2, depends_on=["t1"]),
    ]
    runner = DAGRunner()
    run = runner.run_sync(nodes, run_id="test")
    assert run.success_count == 2
    assert run.status == "done"


def test_prompt_registry_import():
    from prompts.registry import prompt_registry, render_prompt, get_prompt_registry
    reg = get_prompt_registry()
    assert reg is not None
    t = reg.get("system_default")
    assert t is not None
    out = render_prompt("summarize", text="Salam dünya")
    assert out is not None and "Salam" in out


def test_async_client_import():
    from brain.llm.async_client import get_async_client, HAS_HTTPX
    client = get_async_client()
    assert client.model
