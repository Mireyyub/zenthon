#!/usr/bin/env python3
"""Start Leon API under ProcessSupervisor (Phase 10)."""

from __future__ import annotations

import sys
from pathlib import Path

# repo root on path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.supervisor import ProcessSupervisor, SupervisorConfig


def main() -> int:
    cfg = SupervisorConfig.from_env()
    print(f"Leon supervisor → http://{cfg.host}:{cfg.port}")
    print("Ctrl+C to stop.")
    sup = ProcessSupervisor(cfg)
    start = sup.start()
    print(start)
    if not start.get("ok"):
        return 1
    try:
        while True:
            import time

            time.sleep(cfg.poll_interval_s)
            if sup._proc is not None and sup._proc.poll() is not None:
                r = sup.ensure_running()
                print(r)
                if r.get("action") == "give_up":
                    return 2
            else:
                sup.probe_health()
    except KeyboardInterrupt:
        print(sup.stop())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
