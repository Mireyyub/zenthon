#!/usr/bin/env python3
"""Faza 1 qəbul: teach → save → new FactStore → fact görünür."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def main() -> int:
    from core.bootstrap import start_leon, save_state, load_state
    from knowledge.facts import FactStore
    from knowledge.graph import KnowledgeGraph
    from curriculum import CurriculumEngine

    start_leon(check_llm=False, load_persisted=True)
    eng = CurriculumEngine()
    eng.teach("000001", volume_id="01")
    save_state("after_teach")

    fs = FactStore()
    kg = KnowledgeGraph()
    print("facts", len(fs.all()))
    print("graph", kg.stats())
    print("load", load_state())
    ok = len(fs.all()) > 0
    print("PERSIST:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
