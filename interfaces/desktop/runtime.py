"""Combined Tkinter + loopback FastAPI lifecycle for the desktop product."""

from __future__ import annotations

from dataclasses import dataclass, field
import ipaddress
import threading
import time
from typing import Any, Dict, Optional

import uvicorn

from core.logger import logger


def _is_loopback(host: str) -> bool:
    normalized = (host or "").strip().lower()
    if normalized == "localhost":
        return True
    try:
        return ipaddress.ip_address(normalized).is_loopback
    except ValueError:
        return False


@dataclass
class DesktopRuntime:
    """Own the local API thread while the GUI remains on the main thread."""

    host: str = "127.0.0.1"
    port: int = 8000
    bootstrap: bool = True
    startup_timeout_seconds: float = 5.0
    _server: Optional[uvicorn.Server] = field(default=None, init=False, repr=False)
    _thread: Optional[threading.Thread] = field(default=None, init=False, repr=False)
    _startup_report: Dict[str, Any] = field(default_factory=dict, init=False, repr=False)

    def __post_init__(self) -> None:
        if not _is_loopback(self.host):
            raise ValueError("DesktopRuntime only permits a loopback API host")
        if not 1 <= int(self.port) <= 65535:
            raise ValueError("DesktopRuntime port must be between 1 and 65535")

    @property
    def endpoint(self) -> str:
        return f"http://{self.host}:{self.port}"

    @property
    def is_running(self) -> bool:
        return bool(self._server and self._server.started and self._thread and self._thread.is_alive())

    def status(self) -> Dict[str, Any]:
        return {
            "mode": "desktop",
            "api_endpoint": self.endpoint,
            "api_running": self.is_running,
            "startup": self._startup_report,
        }

    def start(self) -> Dict[str, Any]:
        """Bootstrap once, then wait until the loopback bridge is listening."""
        if self.is_running:
            return self.status()

        if self.bootstrap:
            from core.bootstrap import start_leon

            # A local model is optional and must not block opening the desktop UI.
            self._startup_report = start_leon(check_llm=False, load_persisted=True)
        else:
            self._startup_report = {"ok": True, "skipped": True}

        from interfaces.api.main import app

        config = uvicorn.Config(app, host=self.host, port=self.port, log_level="warning", access_log=False)
        self._server = uvicorn.Server(config)
        self._thread = threading.Thread(
            target=self._server.run,
            name="zenthon-loopback-api",
            daemon=True,
        )
        self._thread.start()

        deadline = time.monotonic() + self.startup_timeout_seconds
        while time.monotonic() < deadline:
            if self._server.started:
                from core.event_bus import event_bus

                event_bus.publish(
                    "DesktopRuntimeStarted",
                    {"operation": "loopback-api", "status": "running"},
                    source="desktop",
                )
                logger.info(f"Desktop loopback API started at {self.endpoint}")
                return self.status()
            if not self._thread.is_alive():
                break
            time.sleep(0.05)

        self.stop()
        raise RuntimeError(f"Loopback API could not start at {self.endpoint}")

    def stop(self) -> None:
        """Request an orderly server stop and wait briefly for its thread."""
        server, thread = self._server, self._thread
        if server:
            server.should_exit = True
        if thread and thread.is_alive():
            thread.join(timeout=max(1.0, self.startup_timeout_seconds))
        self._server = None
        self._thread = None
        if server:
            try:
                from core.event_bus import event_bus

                event_bus.publish(
                    "DesktopRuntimeStopped",
                    {"operation": "loopback-api", "status": "stopped"},
                    source="desktop",
                )
            except Exception as error:
                logger.warning(f"Desktop shutdown event could not be published: {error}")

    def run_gui(self) -> None:
        try:
            from interfaces.gui.main_gui import run_gui

            run_gui(on_profile_ready=lambda: str(self.start()["api_endpoint"]))
        finally:
            self.stop()
            try:
                from core.kernel import kernel

                kernel.shutdown()
            except Exception as error:
                logger.warning(f"Desktop kernel shutdown failed: {error}")


def run_desktop(host: str = "127.0.0.1", port: int = 8000) -> None:
    """Run the local desktop application and its companion bridge service."""
    DesktopRuntime(host=host, port=port).run_gui()


def main(argv: Optional[list[str]] = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Zenthon desktop runtime")
    parser.add_argument("--host", default="127.0.0.1", help="Loopback API host")
    parser.add_argument("--port", type=int, default=8000, help="Loopback API port")
    args = parser.parse_args(argv)
    run_desktop(host=args.host, port=args.port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
