"""CLI for system-wide status / improve / smoke."""

from __future__ import annotations

import json
from typing import Any


def run_system(args: Any) -> None:
    from brain.system_loop import SystemLoop

    loop = SystemLoop()
    cmd = getattr(args, "sys_cmd", None) or "status"

    if cmd == "status":
        print(json.dumps(loop.status(), ensure_ascii=False, indent=2, default=str))
        return
    if cmd == "smoke":
        print(json.dumps(loop.smoke(), ensure_ascii=False, indent=2, default=str))
        return
    if cmd == "improve":
        vols = [
            v.strip()
            for v in (getattr(args, "volumes", None) or "01,02").split(",")
            if v.strip()
        ]
        out = loop.improve(
            volumes=vols,
            rounds=int(getattr(args, "rounds", 2) or 2),
            target=float(getattr(args, "target", 0.95) or 0.95),
            with_mutate=bool(getattr(args, "with_mutate", False)),
            with_codegen=bool(getattr(args, "with_codegen", False)),
            dry_run=bool(getattr(args, "dry_run", False)),
        )
        print(json.dumps(out, ensure_ascii=False, indent=2, default=str))
        return

    print("system status|smoke|improve")
