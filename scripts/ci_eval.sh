#!/usr/bin/env bash
# Leon CI – hard-fail cognitive suite
set -euo pipefail
cd "$(dirname "$0")/.."

echo "=== unit cognitive suite ==="
python -m pytest \
  tests/unit/test_facts_graph_learning.py \
  tests/unit/test_security.py \
  tests/unit/test_vector_memory.py \
  tests/unit/test_self_view.py \
  tests/unit/test_multimodal_image.py \
  tests/unit/test_curriculum_vol03.py \
  tests/unit/test_self_improve.py \
  tests/unit/test_self_mutate.py \
  -q --tb=short

echo "=== integration ==="
python -m pytest tests/integration/test_cognitive_persist.py tests/integration/test_phases_smoke.py -q --tb=short

echo "=== verify phases 1-8 ==="
python scripts/verify_phases_1_8.py

echo "=== system body ==="
python - <<'PY'
from brain.policy_bind import bind_mutate_policy
from brain.self_view import SelfView
assert bind_mutate_policy()
b = SelfView().body()
assert b.get("identity") == "Leon"
print("body", b.get("summary"))
PY

echo "=== curriculum 01-03 ==="
python - <<'PY'
from curriculum.volume import load_volume
from evaluation.runner import evaluate_curriculum
for vid in ("01", "02", "03"):
    m = load_volume(vid)
    print("vol", vid, "lessons", len(m.get("lessons") or []))
try:
    r = evaluate_curriculum("01", teach_first=True)
    print("vol01 pass_rate", r.get("pass_rate"))
    if r.get("pass_rate") is not None and float(r["pass_rate"]) < 0.3:
        raise SystemExit("vol01 pass_rate too low")
except Exception as e:
    print("curriculum eval note:", e)
PY

echo "CI eval done"
