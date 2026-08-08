"""Transfer eval + world state + human suite smoke."""

from brain.world_state import WorldState
from evaluation.human_suite import CASES, run_model_answers
from curriculum.volume import load_volume


def test_volumes_04_06():
    for vid in ("04", "05", "06"):
        m = load_volume(vid)
        assert m.get("lessons"), vid


def test_world_state(tmp_path, monkeypatch):
    monkeypatch.setenv("LEON_DATA_DIR", str(tmp_path))
    import core.config as cfg

    cfg.config = cfg.load_config()
    ws = WorldState()
    ws.set_flag("taught_01", True, note="test")
    ws.set_entity("alma", {"category": "meyvə"})
    snap = ws.snapshot()
    assert snap["flags"].get("taught_01") is True
    assert "alma" in snap["entities"]


def test_human_cases_nonempty():
    assert len(CASES) >= 6


def test_transfer_import():
    from evaluation.transfer import transfer_eval

    assert callable(transfer_eval)
