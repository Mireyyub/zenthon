"""One-command local launcher for Leon AI Platform.

Usage:
    python run.py            # creates .venv if needed and starts the local API
    python run.py --check    # creates .venv if needed and runs the core smoke test
    python run.py --desktop  # opens the desktop application with its loopback API
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
OPTIONAL_REQUIREMENTS = {
    "ml": ROOT / "requirements-ml.txt",
    "vision": ROOT / "requirements-vision.txt",
}


def venv_python() -> Path:
    return VENV_DIR / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def ensure_environment(optional_profiles: tuple[str, ...] = ()) -> Path:
    python = venv_python()
    if not python.exists():
        print("[setup] Lokal virtual mühit yaradılır...")
        subprocess.check_call([sys.executable, "-m", "venv", str(VENV_DIR)])

    requirement_files = [REQUIREMENTS, *(OPTIONAL_REQUIREMENTS[name] for name in optional_profiles)]
    fingerprint = hashlib.sha256(
        b"\n".join(path.name.encode("utf-8") + b":" + path.read_bytes() for path in requirement_files)
    ).hexdigest()
    if not STAMP.exists() or STAMP.read_text(encoding="utf-8").strip() != fingerprint:
        labels = " + ".join(("core", *optional_profiles))
        print(f"[setup] {labels} asılılıqları lokal .venv mühitinə quraşdırılır...")
        command = [str(python), "-m", "pip", "install"]
        for path in requirement_files:
            command.extend(["-r", str(path)])
        subprocess.check_call(command, cwd=ROOT)
        STAMP.write_text(fingerprint, encoding="utf-8")
    return python


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Leon AI Platform local runner")
    parser.add_argument("--check", action="store_true", help="Core smoke testini icra et")
    parser.add_argument("--host", default="127.0.0.1", help="API hostu")
    parser.add_argument("--port", type=int, default=8000, help="API portu")
    parser.add_argument("--prepare-ollama", action="store_true", help="Lokal Ollama serverini yoxla və başlat")
    parser.add_argument("--desktop", action="store_true", help="Masaüstü tətbiqi və loopback API-ni birlikdə aç")
    parser.add_argument("--gui", action="store_true", help="Köhnə alias: --desktop")
    parser.add_argument("--with-ml", action="store_true", help="Opsional lokal ML/training paketi quraşdır")
    parser.add_argument("--with-vision", action="store_true", help="Opsional Pillow/OpenCV vision paketi quraşdır")
    parser.add_argument("--with-all", action="store_true", help="Bütün opsional ML və vision paketlərini quraşdır")
    args = parser.parse_args(argv)
    profiles = []
    if args.with_all or args.with_ml:
        profiles.append("ml")
    if args.with_all or args.with_vision:
        profiles.append("vision")
    python = ensure_environment(tuple(profiles))

    if args.prepare_ollama:
        command = [str(python), "scripts/prepare_ollama.py"]
        return subprocess.call(command, cwd=ROOT)

    if args.desktop or args.gui:
        if args.host not in {"127.0.0.1", "::1", "localhost"}:
            parser.error("Masaüstü rejimi yalnız loopback hostunda işləyir")
        command = [
            str(python),
            "-m",
            "interfaces.desktop.runtime",
            "--host",
            args.host,
            "--port",
            str(args.port),
        ]
        print(f"[run] Zenthon masaüstü və local API: http://{args.host}:{args.port}")
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
