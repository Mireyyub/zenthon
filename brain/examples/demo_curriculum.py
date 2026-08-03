"""
LEON Curriculum demo – Existence dərsini öyrət.

    python -m brain.examples.demo_curriculum
"""

import json
from curriculum import CurriculumEngine


def main():
    print("=" * 60)
    print("LEON Curriculum – Lesson 000001 Existence")
    print("=" * 60)

    eng = CurriculumEngine()
    print("Available:", eng.list_available())

    report = eng.teach("000001")
    print(json.dumps(report, ensure_ascii=False, indent=2, default=str))

    print("\n--- Ask ---")
    for q in ["Daş obyektdirmi?", "Alma daşdır?", "İnsan planetdir?"]:
        print(q, "→", eng.ask(q, lesson_id="000001"))

    print("\n--- Classify ---")
    for x in ["alma", "daş", "ulduz", "kompüter"]:
        print(x, "→", eng.classify_objectness(x))

    print("=" * 60)


if __name__ == "__main__":
    main()
