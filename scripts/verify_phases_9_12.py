#!/usr/bin/env python3
"""Verify Phase 9–12 artifacts and light imports."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> int:
    checks = []

    def ok(name: str, cond: bool, detail: str = "") -> None:
        checks.append((name, cond, detail))
        print(("OK  " if cond else "FAIL"), name, detail)

    ok("ui/package.json", (ROOT / "ui" / "package.json").is_file())
    ok("ui/src/api/client.ts", (ROOT / "ui" / "src" / "api" / "client.ts").is_file())
    ok("core/supervisor.py", (ROOT / "core" / "supervisor.py").is_file())
    ok("desktop/tauri seed", (ROOT / "desktop" / "tauri" / "src" / "main.rs").is_file())
    ok("leon_desktop.py", (ROOT / "leon_desktop.py").is_file())
    ok("build_windows.ps1", (ROOT / "scripts" / "build_windows.ps1").is_file())
    ok("Zenthon.nsi", (ROOT / "windows" / "Zenthon.nsi").is_file())
    ok("e2e_desktop_smoke.py", (ROOT / "scripts" / "e2e_desktop_smoke.py").is_file())
    ok("docs/E2E.md", (ROOT / "docs" / "E2E.md").is_file())

    try:
        from core.supervisor import supervisor_status

        st = supervisor_status()
        ok("supervisor_status", st.get("supervisor") is True)
    except Exception as e:
        ok("supervisor_status", False, str(e))

    try:
        import leon_desktop

        ok("leon_desktop.import", callable(leon_desktop.run_desktop))
    except Exception as e:
        ok("leon_desktop.import", False, str(e))

    try:
        from native_core import desktop_status

        d = desktop_status()
        ok("desktop_status.honest", d.get("ready_for_production_desktop") is False)
    except Exception as e:
        ok("desktop_status.honest", False, str(e))

    failed = [c for c in checks if not c[1]]
    print("verify 9-12:", "PASS" if not failed else f"FAIL ({len(failed)})")
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
