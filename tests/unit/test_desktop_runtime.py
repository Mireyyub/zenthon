from __future__ import annotations

import json
import socket
from urllib.request import urlopen

import pytest


def _free_loopback_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def test_desktop_runtime_rejects_non_loopback_host():
    from interfaces.desktop.runtime import DesktopRuntime

    with pytest.raises(ValueError, match="loopback"):
        DesktopRuntime(host="0.0.0.0")


def test_desktop_runtime_starts_and_stops_loopback_api():
    from interfaces.desktop.runtime import DesktopRuntime

    runtime = DesktopRuntime(port=_free_loopback_port(), bootstrap=False)
    try:
        status = runtime.start()
        assert status["api_running"] is True
        with urlopen(f"{runtime.endpoint}/", timeout=3) as response:
            payload = json.loads(response.read().decode("utf-8"))
        assert payload["name"] == "Leon"
    finally:
        runtime.stop()
    assert runtime.is_running is False
