"""Execute one explicitly authorised, guarded self-improvement cycle."""
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
    improvement = self_improve_engine.run_cycle(
        apply_changes=True,
        with_mutate=False,
        with_practice=True,
        with_codegen=False,
    )
    mutation = self_mutate_engine.auto_cycle(
        goal="sual: Lokal LLM nə üçün istifadə olunur? cavab: Mətn əsaslı lokal düşünmə və cavab yaratmaq üçün.",
        apply_best=True,
        from_diagnose=True,
    )
    print(json.dumps({"improvement": improvement, "mutation": mutation}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
