from __future__ import annotations

from pathlib import Path

import pytest


def test_runner_desktop_uses_combined_runtime(monkeypatch):
    import run as runner

    calls = []
    monkeypatch.setattr(runner, "ensure_environment", lambda optional_profiles=(): Path("/venv/python"))
    monkeypatch.setattr(runner.subprocess, "call", lambda command, cwd: calls.append((command, cwd)) or 0)

    assert runner.main(["--desktop", "--port", "8123"]) == 0
    assert calls == [
        (
            ["/venv/python", "-m", "interfaces.desktop.runtime", "--host", "127.0.0.1", "--port", "8123"],
            runner.ROOT,
        )
    ]


def test_runner_desktop_rejects_non_loopback_host(monkeypatch):
    import run as runner

    monkeypatch.setattr(runner, "ensure_environment", lambda optional_profiles=(): Path("/venv/python"))
    with pytest.raises(SystemExit, match="2"):
        runner.main(["--desktop", "--host", "0.0.0.0"])


def test_runner_selects_requested_optional_profiles(monkeypatch):
    import run as runner

    profiles = []
    monkeypatch.setattr(runner, "ensure_environment", lambda optional_profiles=(): profiles.append(optional_profiles) or Path("/venv/python"))
    monkeypatch.setattr(runner.subprocess, "call", lambda command, cwd: 0)

    assert runner.main(["--desktop", "--with-all"]) == 0
    assert profiles == [("ml", "vision")]
