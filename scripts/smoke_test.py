#!/usr/bin/env python3
"""
Faza 0 smoke test.

    python scripts/smoke_test.py
    python -m scripts.smoke_test
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# repo root on path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> int:
    from core.bootstrap import smoke_test

    report = smoke_test()
    print(json.dumps(report, ensure_ascii=False, indent=2, default=str))
    ok = bool(report.get("overall_ok"))
    print("SMOKE:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
