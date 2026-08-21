"""One-command local launcher for Leon AI Platform.

Usage:
    python run.py            # creates .venv if needed and starts the local API
    python run.py --check    # creates .venv if needed and runs the core smoke test
    python run.py --gui      # creates .venv if needed and opens the desktop application
"""

from __future__ import annotations

import argparse
import hashlib
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
VENV_DIR = ROOT / ".venv"
REQUIREMENTS = ROOT / "requirements.txt"
STAMP = VENV_DIR / ".zenthon-requirements.sha256"


def venv_python() -> Path:
    return VENV_DIR / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def ensure_environment() -> Path:
    python = venv_python()
    if not python.exists():
        print("[setup] Lokal virtual mühit yaradılır...")
        subprocess.check_call([sys.executable, "-m", "venv", str(VENV_DIR)])

    fingerprint = hashlib.sha256(REQUIREMENTS.read_bytes()).hexdigest()
    if not STAMP.exists() or STAMP.read_text(encoding="utf-8").strip() != fingerprint:
        print("[setup] Bütün layihə asılılıqları lokal .venv mühitinə quraşdırılır...")
        subprocess.check_call([str(python), "-m", "pip", "install", "-r", str(REQUIREMENTS)], cwd=ROOT)
        STAMP.write_text(fingerprint, encoding="utf-8")
    return python


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Leon AI Platform local runner")
    parser.add_argument("--check", action="store_true", help="Core smoke testini icra et")
    parser.add_argument("--host", default="127.0.0.1", help="API hostu")
    parser.add_argument("--port", type=int, default=8000, help="API portu")
    parser.add_argument("--prepare-ollama", action="store_true", help="Lokal Ollama serverini yoxla və başlat")
    parser.add_argument("--gui", action="store_true", help="Masaüstü qrafik tətbiqini aç")
    args = parser.parse_args(argv)
    python = ensure_environment()

    if args.prepare_ollama:
        command = [str(python), "-c", "from brain.llm.ollama_manager import ensure_ollama; print(ensure_ollama())"]
        return subprocess.call(command, cwd=ROOT)

    if args.gui:
        command = [str(python), "-m", "interfaces.gui.main_gui"]
        print("[run] Zenthon masaüstü tətbiqi başladılır...")
    elif args.check:
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
