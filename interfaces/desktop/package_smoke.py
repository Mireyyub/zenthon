"""GUI-free smoke checks executed against the packaged Windows executable."""

from __future__ import annotations

import json
import socket
from typing import Any, Dict
from urllib.request import urlopen


def _free_loopback_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def core_smoke() -> Dict[str, Any]:
    from core.bootstrap import smoke_test
    from core.kernel import kernel

    try:
        return smoke_test()
    finally:
        kernel.shutdown()


def bridge_smoke() -> Dict[str, Any]:
    from interfaces.desktop.runtime import DesktopRuntime

    runtime = DesktopRuntime(port=_free_loopback_port(), bootstrap=False)
    try:
        status = runtime.start()
        with urlopen(f"{runtime.endpoint}/", timeout=3) as response:
            root = json.loads(response.read().decode("utf-8"))
        return {"ok": status["api_running"] and root.get("name") == "Leon", "status": status, "root": root}
    finally:
        runtime.stop()


def run_and_exit(kind: str) -> int:
    report = core_smoke() if kind == "core" else bridge_smoke()
    print(json.dumps(report, ensure_ascii=False, indent=2, default=str))
    return 0 if report.get("overall_ok", report.get("ok", False)) else 1
