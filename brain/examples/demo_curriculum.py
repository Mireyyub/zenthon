"""
LEON Genesis Curriculum demo – Volume 01 Foundation.

    python -m brain.examples.demo_curriculum
"""

import json
from curriculum import CurriculumEngine


def main():
    print("=" * 60)
    print("LEON Genesis Curriculum – Volume 01 Foundation")
    print("=" * 60)

    eng = CurriculumEngine()
    print("Volumes:", eng.list_volumes())
    print("Lessons:", eng.list_available("01"))

    report = eng.teach_volume("01")
    # compact print
    summary = {
        "volume": report.get("volume"),
        "name": report.get("name"),
        "target_concepts": report.get("target_concepts"),
        "lessons_taught": report.get("lessons_taught"),
        "lessons_passed": report.get("lessons_passed"),
        "lessons_total": report.get("lessons_total"),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))

    print("\n--- Classify ---")
    for x in ["alma", "rəng", "heyvan", "is_a", "mövcudluq"]:
        print(f"  {x} → {eng.classify(x)}")

    print("=" * 60)


if __name__ == "__main__":
    main()
