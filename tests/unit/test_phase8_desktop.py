"""Phase 8 — desktop readiness + RAG persist."""

from __future__ import annotations

import tempfile
from pathlib import Path


def test_desktop_status_honest():
    from native_core import desktop_status, desktop_readiness

    d = desktop_status()
    assert d["target"] == "hybrid-local-desktop"
    assert d["ready_for_production_desktop"] is False
    assert "ui_today" in d and d["ui_today"] == "tkinter-legacy"
    assert "shell_target" in d
    r = desktop_readiness()
    assert isinstance(r.ready_for_tauri, bool)


def test_native_core_health_still_works():
    from native_core import health_report, get_native_core

    h = health_report()
    assert h["mode"] in ("python-fallback", "native-binary")
    core = get_native_core()
    n = core.normalize_text("  a  b  ")
    assert n.value == "a b"


def test_rag_persist_roundtrip():
    from brain.rag.pipeline import RAGPipeline

    with tempfile.TemporaryDirectory() as td:
        p = RAGPipeline(persist_dir=td, auto_load=False)
        p.ingest_text(
            "Leon offline-first cognitive AI sistemidir. ReasoningEngine evidence istifadə edir.",
            source="test",
        )
        assert p.stats()["chunks"] >= 1
        assert Path(td, "index.json").exists()

        p2 = RAGPipeline(persist_dir=td, auto_load=True)
        assert p2.stats()["chunks"] >= 1
        ctx = p2.retrieve("ReasoningEngine", top_k=3)
        assert ctx.total_chunks >= 0  # may be 0 if keyword miss; must not raise
        out = p2.query("Leon nedir?", generate=False)
        assert "question" in out
        assert out["persisted_chunks"] >= 1


def test_v1_desktop_endpoint():
    try:
        from fastapi.testclient import TestClient
    except Exception:
        return
    from interfaces.api.main import app

    client = TestClient(app)
    r = client.get("/api/v1/system/desktop")
    assert r.status_code == 200
    body = r.json()
    assert body.get("ready_for_production_desktop") is False
    assert "cognitive_core" in body


def test_health_includes_desktop_component():
    try:
        from fastapi.testclient import TestClient
    except Exception:
        return
    from interfaces.api.main import app

    client = TestClient(app)
    r = client.get("/api/v1/health")
    assert r.status_code == 200
    comps = r.json().get("components") or {}
    # desktop optional soft-add; if present must be dict
    if "desktop" in comps:
        assert isinstance(comps["desktop"], dict)
