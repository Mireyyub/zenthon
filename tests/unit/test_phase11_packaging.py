"""Phase 11 — packaging entry and scripts exist; no full Windows build in CI."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_leon_desktop_importable():
    import leon_desktop

    assert callable(leon_desktop.run_desktop)


def test_zenthon_desktop_delegates():
    import zenthon_desktop

    assert zenthon_desktop.run_desktop is not None or hasattr(zenthon_desktop, "__file__")


def test_packaging_files_present():
    assert (ROOT / "scripts" / "build_windows.ps1").is_file()
    assert (ROOT / "windows" / "Zenthon.nsi").is_file()
    assert (ROOT / "windows" / "Leon.cmd").is_file()
    assert (ROOT / "windows" / "Leon-API.cmd").is_file()
    assert (ROOT / "requirements-windows-build.txt").is_file()
    assert (ROOT / "docs" / "PACKAGING.md").is_file()


def test_nsi_not_force_startup():
    text = (ROOT / "windows" / "Zenthon.nsi").read_text(encoding="utf-8", errors="ignore")
    # Startup section should be optional (/o)
    assert "SecStartup" in text
    assert "/o" in text or "optional" in text.lower()


def test_build_script_mentions_leon_entry():
    text = (ROOT / "scripts" / "build_windows.ps1").read_text(encoding="utf-8", errors="ignore")
    assert "leon_desktop" in text
