"""Self-mutate allowlist + syntax gate."""

from __future__ import annotations

import os
from pathlib import Path

import pytest


def test_forbidden_security(tmp_path, monkeypatch):
    from brain.self_mutate import SelfMutateEngine

    eng = SelfMutateEngine(repo_root=tmp_path)
    (tmp_path / "security").mkdir()
    (tmp_path / "security" / "allowlist.py").write_text("x=1\n", encoding="utf-8")
    r = eng.propose("security/allowlist.py", mode="write", content="x=2\n")
    assert r.get("ok") is False


def test_append_train_and_apply(tmp_path, monkeypatch):
    from brain.self_mutate import SelfMutateEngine

    eng = SelfMutateEngine(repo_root=tmp_path)
    rel = "curriculum/volumes/01_foundation/train.jsonl"
    p = tmp_path / rel
    p.parent.mkdir(parents=True)
    p.write_text('{"id":"1"}\n', encoding="utf-8")

    # mutation dir under tmp via env
    monkeypatch.setenv("LEON_DATA_DIR", str(tmp_path / "data"))
    import core.config as cfg

    cfg.config = cfg.load_config()
    eng = SelfMutateEngine(repo_root=tmp_path)

    prop = eng.propose(rel, mode="append", new='{"id":"2"}\n', reason="test")
    assert prop.get("ok") is True
    monkeypatch.setenv("LEON_ALLOW_MUTATE", "1")
    eng2 = SelfMutateEngine(repo_root=tmp_path)
    applied = eng2.apply(prop["proposal_id"], run_smoke=False)
    assert applied.get("ok") is True
    assert '"id":"2"' in p.read_text(encoding="utf-8")
