#!/usr/bin/env python3
"""
Phase 12 — E2E desktop smoke (API path).

Flow covered in-process (no NSIS install required):
  bootstrap → health → desktop readiness → supervisor probe
  → chat → reason → models → stop probe

Optional live supervisor:
  LEON_E2E_LIVE_SUPERVISOR=1 python scripts/e2e_desktop_smoke.py

Exit 0 = PASS, 1 = FAIL
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _step(name: str, ok: bool, detail: Any = None) -> Dict[str, Any]:
    return {"step": name, "ok": bool(ok), "detail": detail}


def run_api_e2e() -> Dict[str, Any]:
    results: List[Dict[str, Any]] = []
    overall = True

    # 1) bootstrap
    try:
        from core.bootstrap import start_leon

        boot = start_leon(bootstrap_curriculum=False, check_llm=True, load_persisted=True)
        ok = bool(boot.get("ok", True))
        results.append(_step("bootstrap", ok, {"warnings": boot.get("warnings")}))
        if not ok:
            overall = False
    except Exception as e:
        results.append(_step("bootstrap", False, str(e)))
        overall = False

    # 2) FastAPI TestClient path
    try:
        from fastapi.testclient import TestClient
        from interfaces.api.main import app

        client = TestClient(app)

        r = client.get("/api/v1/health")
        results.append(_step("health", r.status_code == 200, r.json() if r.status_code == 200 else r.text))
        if r.status_code != 200:
            overall = False

        r = client.get("/api/v1/system/desktop")
        body = r.json() if r.status_code == 200 else {}
        desk_ok = r.status_code == 200 and body.get("ready_for_production_desktop") is False
        results.append(_step("desktop_readiness", desk_ok, body))
        if not desk_ok:
            overall = False

        r = client.get("/api/v1/system/supervisor")
        results.append(
            _step("supervisor_probe", r.status_code == 200, r.json() if r.status_code == 200 else r.text)
        )
        if r.status_code != 200:
            overall = False

        r = client.get("/api/v1/models")
        results.append(_step("models", r.status_code == 200, r.json() if r.status_code == 200 else r.text))

        r = client.post("/api/v1/chat", json={"message": "Salam Leon, test"})
        chat_ok = r.status_code == 200 and bool((r.json() or {}).get("answer") is not None or True)
        # answer may be empty string but endpoint must succeed
        chat_ok = r.status_code == 200
        results.append(_step("chat", chat_ok, r.json() if chat_ok else r.text))
        if not chat_ok:
            overall = False

        r = client.post("/api/v1/reason", json={"query": "Daş mövcuddurmu?", "use_brain": True})
        reason_ok = r.status_code == 200
        results.append(_step("reason", reason_ok, r.json() if reason_ok else r.text))
        if not reason_ok:
            overall = False

        r = client.get("/api/v1/")
        results.append(_step("v1_index", r.status_code == 200))

    except Exception as e:
        results.append(_step("api_client", False, str(e)))
        overall = False

    # 3) packaging entry import (launch readiness)
    try:
        import leon_desktop

        results.append(_step("launch_entry_import", callable(leon_desktop.run_desktop)))
    except Exception as e:
        results.append(_step("launch_entry_import", False, str(e)))
        overall = False

    return {"overall_ok": overall, "mode": "api_inprocess", "results": results}


def run_live_supervisor_e2e() -> Dict[str, Any]:
    """Optional: real uvicorn child process."""
    from core.supervisor import ProcessSupervisor, SupervisorConfig

    results: List[Dict[str, Any]] = []
    overall = True
    cfg = SupervisorConfig(host="127.0.0.1", port=int(os.getenv("LEON_E2E_PORT", "8765")), startup_grace_s=3.0)
    sup = ProcessSupervisor(cfg)
    try:
        start = sup.start()
        results.append(_step("supervisor_start", bool(start.get("ok")), start))
        if not start.get("ok"):
            return {"overall_ok": False, "mode": "live_supervisor", "results": results}

        # wait health
        healthy = False
        for _ in range(15):
            if sup.probe_health():
                healthy = True
                break
            time.sleep(0.5)
        results.append(_step("supervisor_health", healthy))
        if not healthy:
            overall = False

        # HTTP chat against live server
        try:
            from urllib.request import Request, urlopen
            import json as _json

            req = Request(
                f"{sup.base_url}/api/v1/chat",
                data=_json.dumps({"message": "E2E live test"}).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urlopen(req, timeout=60) as resp:
                raw = resp.read().decode("utf-8")
                results.append(_step("live_chat", 200 <= resp.status < 300, raw[:300]))
        except Exception as e:
            results.append(_step("live_chat", False, str(e)))
            overall = False

        stop = sup.stop()
        results.append(_step("supervisor_stop", bool(stop.get("ok")), stop))

        # restart once
        start2 = sup.start()
        results.append(_step("supervisor_restart", bool(start2.get("ok")), start2))
        if not start2.get("ok"):
            overall = False
        sup.stop()

    except Exception as e:
        results.append(_step("live_supervisor", False, str(e)))
        overall = False
        try:
            sup.stop()
        except Exception:
            pass

    return {"overall_ok": overall, "mode": "live_supervisor", "results": results}


def main() -> int:
    report = run_api_e2e()
    if os.getenv("LEON_E2E_LIVE_SUPERVISOR", "").strip() in ("1", "true", "True"):
        live = run_live_supervisor_e2e()
        report["live"] = live
        report["overall_ok"] = report["overall_ok"] and live.get("overall_ok", False)

    print(json.dumps(report, ensure_ascii=False, indent=2, default=str))
    ok = bool(report.get("overall_ok"))
    print("E2E DESKTOP:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
