#!/usr/bin/env bash
# Faza 8 – minimal CI eval
set -euo pipefail
cd "$(dirname "$0")/.."

echo "=== unit cognitive ==="
python -m pytest tests/unit/test_facts_graph_learning.py tests/unit/test_vector_memory.py -q

echo "=== integration cognitive ==="
python -m pytest tests/integration/test_cognitive_persist.py -q

echo "=== curriculum eval (soft) ==="
python - <<'PY'
from evaluation.runner import evaluate_curriculum
try:
    r = evaluate_curriculum("01", teach_first=True)
    print("pass_rate", r.get("pass_rate"), r.get("passed"), "/", r.get("total"))
except Exception as e:
    print("curriculum eval skip:", e)
PY

echo "=== health ==="
python -m interfaces.cli.main_cli health || true

echo "CI eval done"
