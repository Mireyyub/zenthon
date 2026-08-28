"""
Leon desktop entry (Phase 11).

Windows / PyInstaller primary entry:
1) ensure paths
2) start local API under ProcessSupervisor (127.0.0.1)
3) open Tkinter GUI (legacy, working today)
4) optional browser to React UI if LEON_OPEN_UI=1

No AI logic here — only process + UI shell.
"""

from __future__ import annotations

import atexit
import os
import sys
import threading
import time
import webbrowser
from typing import Any, Dict, Optional


def _bootstrap() -> Dict[str, Any]:
    try:
        from core.bootstrap import start_leon

        return start_leon(
            bootstrap_curriculum=False,
            check_llm=True,
            load_persisted=True,
        )
    except Exception as e:
        return {"ok": False, "error": str(e)}


def _start_api_background() -> Optional[Any]:
    if os.getenv("LEON_DESKTOP_NO_API", "").strip() in ("1", "true", "True"):
        return None
    try:
        from core.supervisor import ProcessSupervisor, SupervisorConfig

        cfg = SupervisorConfig.from_env()
        # Force localhost for desktop safety
        cfg.host = "127.0.0.1"
        sup = ProcessSupervisor(cfg)
        res = sup.start()
        if res.get("ok"):
            atexit.register(lambda: sup.stop())
            return sup
        return None
    except Exception:
        return None


def _maybe_open_browser() -> None:
    if os.getenv("LEON_OPEN_UI", "").strip() not in ("1", "true", "True"):
        return

    def _open() -> None:
        time.sleep(1.5)
        url = os.getenv("LEON_UI_URL", "http://127.0.0.1:5173").strip()
        try:
            webbrowser.open(url)
        except Exception:
            try:
                webbrowser.open("http://127.0.0.1:8000/docs")
            except Exception:
                pass

    threading.Thread(target=_open, daemon=True).start()


def run_desktop() -> None:
    report = _bootstrap()
    if not report.get("ok"):
        # Still try GUI — bootstrap warnings are soft for desktop
        pass

    sup = _start_api_background()
    _maybe_open_browser()

    # Primary UX today: Tkinter (Phase 9 React is separate npm process)
    try:
        from interfaces.gui.main_gui import run_gui

        run_gui()
    except Exception as e:
        # Headless / missing Tk — keep API alive briefly for debug
        print(f"Leon desktop GUI failed: {e}", file=sys.stderr)
        if sup is not None:
            print("API supervisor running at http://127.0.0.1:8000 — Ctrl+C to exit")
            try:
                while True:
                    time.sleep(2)
                    if hasattr(sup, "probe_health"):
                        sup.probe_health()
            except KeyboardInterrupt:
                pass
        else:
            raise


if __name__ == "__main__":
    run_desktop()
