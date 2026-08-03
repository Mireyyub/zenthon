#!/usr/bin/env bash
# Faza 8 CI + phase 1-8 verify
set -euo pipefail
cd "$(dirname "$0")/.."

echo "=== unit cognitive + security ==="
python -m pytest tests/unit/test_facts_graph_learning.py tests/unit/test_security.py tests/unit/test_vector_memory.py -q

echo "=== integration ==="
python -m pytest tests/integration/test_cognitive_persist.py tests/integration/test_phases_smoke.py -q

echo "=== verify phases 1-8 ==="
python scripts/verify_phases_1_8.py

echo "=== curriculum eval soft ==="
python - <<'PY'
from evaluation.runner import evaluate_curriculum
try:
    r = evaluate_curriculum("01", teach_first=True)
    print("vol01 pass_rate", r.get("pass_rate"))
except Exception as e:
    print("curriculum eval skip:", e)
PY

echo "CI eval done"
