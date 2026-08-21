"""One-command local launcher for Leon AI Platform.

Usage:
    python run.py            # creates .venv if needed and starts the local API
    python run.py --check    # creates .venv if needed and runs the core smoke test
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
VENV_DIR = ROOT / ".venv"


def venv_python() -> Path:
    return VENV_DIR / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def ensure_environment() -> Path:
    python = venv_python()
    if not python.exists():
        print("[setup] Lokal virtual mühit yaradılır...")
        subprocess.check_call([sys.executable, "-m", "venv", str(VENV_DIR)])

    probe = subprocess.run(
        [str(python), "-c", "import fastapi, numpy, pandas, pydantic, uvicorn"],
        cwd=ROOT,
        check=False,
    )
    if probe.returncode != 0:
        print("[setup] Asılılıqlar quraşdırılır...")
        subprocess.check_call([str(python), "-m", "pip", "install", "-r", "requirements.txt"], cwd=ROOT)
    return python


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Leon AI Platform local runner")
    parser.add_argument("--check", action="store_true", help="Core smoke testini icra et")
    parser.add_argument("--host", default="127.0.0.1", help="API hostu")
    parser.add_argument("--port", type=int, default=8000, help="API portu")
    args = parser.parse_args(argv)
    python = ensure_environment()

    if args.check:
        command = [str(python), "zenthon_app.py", "--smoke", "--no-llm-check"]
    else:
        command = [
            str(python),
            "-m",
            "uvicorn",
            "interfaces.api.main:app",
            "--host",
            args.host,
            "--port",
            str(args.port),
        ]
        print(f"[run] Leon API: http://{args.host}:{args.port}/docs")

    return subprocess.call(command, cwd=ROOT)


if __name__ == "__main__":
    raise SystemExit(main())
