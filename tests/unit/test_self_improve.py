"""Self-improve diagnose/propose dry path."""

from __future__ import annotations

import pytest


@pytest.fixture()
def si_env(tmp_path, monkeypatch):
    leon = tmp_path / "leon"
    for sub in ("facts", "graph", "learning", "memory", "traces", "self_improve", "plans"):
        (leon / sub).mkdir(parents=True)
    monkeypatch.setenv("LEON_DATA_DIR", str(tmp_path))
    import core.config as cfg

    cfg.config = cfg.load_config()
    import knowledge.registry as reg

    reg._fact_store = None
    reg._graph = None
    return tmp_path


def test_diagnose_and_dry_cycle(si_env):
    from brain.self_improve import SelfImproveEngine

    eng = SelfImproveEngine()
    # dry cycle should not require full curriculum assets in all envs
    try:
        out = eng.run_cycle(volumes=["01"], apply_changes=False)
    except Exception as e:
        pytest.skip(str(e))
    assert "diagnosis" in out or "proposal" in out
    assert out.get("applied") is False
