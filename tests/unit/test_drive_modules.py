"""Smoke tests for Drive-integrated modules (dag_runner, decision_engine, prompt registry)."""
from __future__ import annotations

import pytest


def test_decision_engine_basic():
    from agents.decision_engine import DecisionEngine

    eng = DecisionEngine()
    alts = [
        {
            "id": "fast",
            "description": "Sürətli yol",
            "scores": {"accuracy": 0.6, "latency": 0.95, "compute": 0.9, "reliability": 0.7, "complexity": 0.8},
        },
        {
            "id": "accurate",
            "description": "Dəqiq yol",
            "scores": {"accuracy": 0.95, "latency": 0.4, "compute": 0.5, "reliability": 0.9, "complexity": 0.5},
        },
    ]
    result = eng.decide(alts, task_type="critical")
    assert result.winner.id == "accurate"
    assert result.margin >= 0


def test_dag_runner_sync():
    from brain.planning.dag_runner import DAGRunner, DAGNode

    def step_a(dep_results=None):
        return 10

    def step_b(dep_results=None):
        return (dep_results or {}).get("a", 0) + 5

    nodes = [
        DAGNode(id="a", label="A", func=step_a),
        DAGNode(id="b", label="B", func=step_b, depends_on=["a"]),
    ]
    runner = DAGRunner()
    run = runner.run_sync(nodes, run_id="t1")
    assert run.status in ("done", "partial")
    assert run.nodes["a"].status == "done"
    assert run.nodes["a"].result == 10
    assert run.nodes["b"].result == 15


def test_prompt_registry_render():
    from prompts.registry import prompt_registry, render_prompt

    out = render_prompt("summarize", text="Leon kognitiv sistemdir.")
    assert out is not None
    assert "Leon" in out or "xülasə" in out.lower() or "Xülasə" in out
    assert prompt_registry.get("system_default") is not None
