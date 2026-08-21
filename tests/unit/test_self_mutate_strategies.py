from pathlib import Path


def test_qa_pair_strategy_creates_high_confidence_training_record(tmp_path, monkeypatch):
    from brain.self_mutate import SelfMutateEngine
    import core.config as cfg

    monkeypatch.setenv("LEON_DATA_DIR", str(tmp_path / "data"))
    cfg.config = cfg.load_config()
    target = tmp_path / "curriculum/volumes/01_foundation/train.jsonl"
    target.parent.mkdir(parents=True)
    target.write_text("", encoding="utf-8")
    result = SelfMutateEngine(repo_root=tmp_path).propose_strategy(
        "qa_pair_append", goal="sual: 2+2? cavab: 4", path=str(target.relative_to(tmp_path))
    )
    assert result["ok"] is True
    assert result["strategy"] == "qa_pair_append"


def test_qa_pair_strategy_rejects_unstructured_goal(tmp_path):
    from brain.self_mutate import SelfMutateEngine

    result = SelfMutateEngine(repo_root=tmp_path).propose_strategy("qa_pair_append", goal="sadə fakt")
    assert result["ok"] is False
