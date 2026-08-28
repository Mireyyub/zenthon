"""Phase 12 — E2E desktop API flow (in-process)."""

from __future__ import annotations


def test_e2e_desktop_smoke_api():
    from scripts.e2e_desktop_smoke import run_api_e2e

    report = run_api_e2e()
    assert report["overall_ok"] is True, report
    steps = {s["step"]: s["ok"] for s in report["results"]}
    assert steps.get("health") is True
    assert steps.get("chat") is True
    assert steps.get("reason") is True
    assert steps.get("desktop_readiness") is True
    assert steps.get("launch_entry_import") is True


def test_packaging_checklist_docs_exist():
    from pathlib import Path

    root = Path(__file__).resolve().parents[2]
    assert (root / "docs" / "E2E.md").is_file()
    assert (root / "docs" / "PACKAGING.md").is_file()
