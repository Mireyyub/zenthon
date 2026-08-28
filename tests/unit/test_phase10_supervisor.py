"""Phase 10 — process supervisor (no AI, lifecycle only)."""

from __future__ import annotations

from core.supervisor import ProcessSupervisor, SupervisorConfig, supervisor_status


def test_supervisor_status_dict():
    st = supervisor_status()
    assert st.get("supervisor") is True
    assert "base_url" in st
    assert "config" in st


def test_config_from_env_defaults(monkeypatch):
    monkeypatch.delenv("LEON_API_HOST", raising=False)
    monkeypatch.delenv("LEON_API_PORT", raising=False)
    cfg = SupervisorConfig.from_env()
    assert cfg.host == "127.0.0.1"
    assert cfg.port == 8000
    assert cfg.max_restarts >= 1


def test_probe_health_soft_when_down():
    cfg = SupervisorConfig(host="127.0.0.1", port=59999, health_timeout_s=0.3)
    sup = ProcessSupervisor(cfg)
    ok = sup.probe_health()
    assert ok is False
    assert sup.state.last_health_ok is False


def test_stop_without_start():
    sup = ProcessSupervisor(SupervisorConfig())
    r = sup.stop()
    assert r.get("ok") is True
    assert r.get("running") is False


def test_max_restarts_give_up():
    cfg = SupervisorConfig(max_restarts=0)
    sup = ProcessSupervisor(cfg)
    sup.state.restarts = 0
    # simulate dead process without starting
    sup._proc = None
    r = sup.ensure_running()
    # with max_restarts 0, first ensure may try start; force restarts high
    sup.state.restarts = 99
    r2 = sup.ensure_running()
    assert r2.get("action") == "give_up" or r2.get("ok") is False


def test_v1_supervisor_endpoint():
    try:
        from fastapi.testclient import TestClient
    except Exception:
        return
    from interfaces.api.main import app

    client = TestClient(app)
    r = client.get("/api/v1/system/supervisor")
    assert r.status_code == 200
    body = r.json()
    assert body.get("supervisor") is True
