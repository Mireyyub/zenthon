"""Run a non-writing source-code simulation of self-improvement pathways."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from brain.self_improve import self_improve_engine
from brain.self_mutate import self_mutate_engine


def main() -> None:
    improve = self_improve_engine.auto(rounds=2, target=0.95, dry_run=True)
    mutate = self_mutate_engine.auto_cycle(
        goal="sual: Lokal LLM nə üçün istifadə olunur? cavab: Mətn əsaslı lokal düşünmə və cavab yaratmaq üçün.",
        apply_best=False,
        from_diagnose=True,
    )
    print(json.dumps({"source_changes_applied": False, "self_improve": improve, "mutation": mutate}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
