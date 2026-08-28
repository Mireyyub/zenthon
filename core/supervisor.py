"""
Process supervisor (Phase 10).

Owns lifecycle of the local FastAPI backend — not AI logic.
- Start uvicorn on 127.0.0.1
- Poll /api/v1/health
- Restart with exponential backoff, capped attempts
- Soft Ollama probe (never fail hard if offline)

Tauri shell (desktop/tauri) is expected to call into this module
or spawn `python -m core.supervisor` — Rust must not reimplement reasoning.
"""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.error import URLError
from urllib.request import urlopen

from core.logger import logger


@dataclass
class SupervisorConfig:
    host: str = "127.0.0.1"
    port: int = 8000
    module: str = "interfaces.api.main:app"
    health_path: str = "/api/v1/health"
    health_timeout_s: float = 2.0
    startup_grace_s: float = 2.0
    poll_interval_s: float = 3.0
    max_restarts: int = 5
    backoff_base_s: float = 1.5
    backoff_cap_s: float = 30.0
    check_ollama: bool = True
    ollama_url: str = "http://127.0.0.1:11434/api/tags"

    @classmethod
    def from_env(cls) -> "SupervisorConfig":
        return cls(
            host=os.getenv("LEON_API_HOST", "127.0.0.1").strip() or "127.0.0.1",
            port=int(os.getenv("LEON_API_PORT", "8000") or "8000"),
            max_restarts=int(os.getenv("LEON_SUPERVISOR_MAX_RESTARTS", "5") or "5"),
            check_ollama=os.getenv("LEON_SUPERVISOR_CHECK_OLLAMA", "1") not in (
                "0",
                "false",
                "False",
            ),
        )


@dataclass
class SupervisorState:
    running: bool = False
    pid: Optional[int] = None
    restarts: int = 0
    last_health_ok: bool = False
    last_error: Optional[str] = None
    ollama_reachable: Optional[bool] = None
    started_at: Optional[float] = None
    history: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "running": self.running,
            "pid": self.pid,
            "restarts": self.restarts,
            "last_health_ok": self.last_health_ok,
            "last_error": self.last_error,
            "ollama_reachable": self.ollama_reachable,
            "started_at": self.started_at,
            "history": list(self.history[-12:]),
        }


class ProcessSupervisor:
    """Local API process owner. No cognitive code here."""

    def __init__(self, config: Optional[SupervisorConfig] = None):
        self.config = config or SupervisorConfig.from_env()
        self.state = SupervisorState()
        self._proc: Optional[subprocess.Popen[str]] = None

    @property
    def base_url(self) -> str:
        return f"http://{self.config.host}:{self.config.port}"

    def health_url(self) -> str:
        return f"{self.base_url}{self.config.health_path}"

    def probe_health(self) -> bool:
        try:
            with urlopen(self.health_url(), timeout=self.config.health_timeout_s) as resp:
                ok = 200 <= getattr(resp, "status", 200) < 300
                self.state.last_health_ok = ok
                if not ok:
                    self.state.last_error = f"health status {getattr(resp, 'status', '?')}"
                return ok
        except Exception as e:
            self.state.last_health_ok = False
            self.state.last_error = str(e)
            return False

    def probe_ollama(self) -> bool:
        if not self.config.check_ollama:
            self.state.ollama_reachable = None
            return False
        try:
            with urlopen(self.config.ollama_url, timeout=1.5) as resp:
                ok = 200 <= getattr(resp, "status", 200) < 300
                self.state.ollama_reachable = ok
                return ok
        except Exception:
            self.state.ollama_reachable = False
            return False

    def _note(self, msg: str) -> None:
        logger.info(f"supervisor: {msg}")
        self.state.history.append(f"{time.strftime('%H:%M:%S')} {msg}")

    def start(self) -> Dict[str, Any]:
        if self._proc is not None and self._proc.poll() is None:
            return {"ok": True, "already_running": True, **self.status()}

        if self.config.host not in ("127.0.0.1", "localhost", "::1"):
            # Soft warning only — env may intentionally open LAN
            self._note(f"host={self.config.host} (prefer 127.0.0.1 for desktop)")

        cmd = [
            sys.executable,
            "-m",
            "uvicorn",
            self.config.module,
            "--host",
            self.config.host,
            "--port",
            str(self.config.port),
            "--log-level",
            "warning",
        ]
        self._note(f"starting: {' '.join(cmd)}")
        try:
            self._proc = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                text=True,
                cwd=str(Path.cwd()),
            )
        except Exception as e:
            self.state.last_error = str(e)
            self.state.running = False
            return {"ok": False, "error": str(e), **self.status()}

        self.state.pid = self._proc.pid
        self.state.running = True
        self.state.started_at = time.time()
        time.sleep(self.config.startup_grace_s)
        healthy = self.probe_health()
        self.probe_ollama()
        if not healthy:
            self._note("process up but health not ready yet")
        return {"ok": True, "health": healthy, **self.status()}

    def stop(self, timeout_s: float = 5.0) -> Dict[str, Any]:
        if self._proc is None:
            self.state.running = False
            self.state.pid = None
            return {"ok": True, "stopped": True, **self.status()}

        proc = self._proc
        self._note(f"stopping pid={proc.pid}")
        try:
            if sys.platform == "win32":
                proc.terminate()
            else:
                proc.send_signal(signal.SIGTERM)
            try:
                proc.wait(timeout=timeout_s)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=2)
        except Exception as e:
            self.state.last_error = str(e)
            try:
                proc.kill()
            except Exception:
                pass

        self._proc = None
        self.state.running = False
        self.state.pid = None
        self.state.last_health_ok = False
        return {"ok": True, "stopped": True, **self.status()}

    def ensure_running(self) -> Dict[str, Any]:
        """Start if needed; restart if dead and under max_restarts."""
        if self._proc is not None and self._proc.poll() is None:
            if self.probe_health():
                return {"ok": True, "action": "healthy", **self.status()}
            # process alive but health fail — do not restart immediately
            return {"ok": True, "action": "waiting_health", **self.status()}

        if self.state.restarts >= self.config.max_restarts:
            self.state.last_error = "max_restarts exceeded"
            return {"ok": False, "action": "give_up", **self.status()}

        if self._proc is not None and self._proc.poll() is not None:
            self.state.restarts += 1
            delay = min(
                self.config.backoff_cap_s,
                self.config.backoff_base_s ** min(self.state.restarts, 6),
            )
            self._note(f"process exited; restart #{self.state.restarts} in {delay:.1f}s")
            time.sleep(delay)

        return {"action": "start", **self.start()}

    def run_forever(self, max_ticks: Optional[int] = None) -> Dict[str, Any]:
        """Blocking supervise loop. max_ticks for tests."""
        self.start()
        ticks = 0
        try:
            while True:
                ticks += 1
                if max_ticks is not None and ticks > max_ticks:
                    break
                if self._proc is not None and self._proc.poll() is not None:
                    res = self.ensure_running()
                    if not res.get("ok") and res.get("action") == "give_up":
                        break
                else:
                    self.probe_health()
                time.sleep(self.config.poll_interval_s)
        except KeyboardInterrupt:
            self._note("interrupted")
        finally:
            self.stop()
        return self.status()

    def status(self) -> Dict[str, Any]:
        alive = self._proc is not None and self._proc.poll() is None
        self.state.running = alive
        if alive and self._proc is not None:
            self.state.pid = self._proc.pid
        return {
            "supervisor": True,
            "base_url": self.base_url,
            "config": {
                "host": self.config.host,
                "port": self.config.port,
                "max_restarts": self.config.max_restarts,
                "module": self.config.module,
            },
            **self.state.to_dict(),
        }


_supervisor: Optional[ProcessSupervisor] = None


def get_supervisor(force_new: bool = False) -> ProcessSupervisor:
    global _supervisor
    if _supervisor is None or force_new:
        _supervisor = ProcessSupervisor()
    return _supervisor


def supervisor_status() -> Dict[str, Any]:
    """Read-only status; does not start processes."""
    s = get_supervisor()
    # probe external health without owning process
    external_ok = s.probe_health()
    s.probe_ollama()
    out = s.status()
    out["external_api_reachable"] = external_ok
    out["note"] = (
        "This endpoint reports probe state; "
        "managed process only exists if supervisor.start() was called in this process."
    )
    return out


def main() -> None:
    cfg = SupervisorConfig.from_env()
    sup = ProcessSupervisor(cfg)
    print(sup.start())
    try:
        while True:
            time.sleep(cfg.poll_interval_s)
            if sup._proc is not None and sup._proc.poll() is not None:
                r = sup.ensure_running()
                print(r)
                if not r.get("ok") and r.get("action") == "give_up":
                    break
            else:
                sup.probe_health()
    except KeyboardInterrupt:
        print(sup.stop())


if __name__ == "__main__":
    main()
