"""Windows/PyInstaller entry point for the Zenthon desktop application."""
from __future__ import annotations

import sys

from interfaces.desktop.runtime import run_desktop


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    if args == ["--smoke"]:
        from interfaces.desktop.package_smoke import run_and_exit

        return run_and_exit("core")
    if args == ["--bridge-smoke"]:
        from interfaces.desktop.package_smoke import run_and_exit

        return run_and_exit("bridge")
    if args:
        print("Usage: Zenthon.exe [--smoke | --bridge-smoke]", file=sys.stderr)
        return 2
    run_desktop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
