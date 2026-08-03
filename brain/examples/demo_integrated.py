"""
Specs + Curriculum + Engines inteqrasiya demosu.

    python -m brain.examples.demo_integrated
"""

import json
from learning import bootstrap_from_specs, learning_engine
from brain.reasoning.engine import reasoning_engine
from genome.loader import list_genes, load_all_genes


def main():
    print("=" * 64)
    print("LEON Integrated Bootstrap (specs + curriculum + engines)")
    print("=" * 64)

    print("Genes:", list_genes())
    for g in load_all_genes():
        print(f"  {g.get('id')}: {g.get('name')} — {g.get('definition')}")

    report = bootstrap_from_specs("01")
    summary = {
        "genes_activated": report.get("genes_activated"),
        "volume": (report.get("volume") or {}).get("name"),
        "lessons_passed": (report.get("volume") or {}).get("lessons_passed"),
        "learning": report.get("learning_stats"),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))

    print("\n--- ReasoningEngine ---")
    for q in ["Daş mövcuddurmu?", "Alma hansı kateqoriyaya daxildir?", "Ay nə ətrafında fırlanır?"]:
        r = reasoning_engine.reason(q)
        print(f"Q: {q}")
        print(f"A: {r['answer']} | conf={r['confidence']} | strategy={r['strategy']}")

    print("\n--- LearningEngine ---")
    lr = learning_engine.learn("LEON Foundation tamamlandı", source="demo", confidence=0.9)
    print(lr["record"]["status"], lr["record"]["id"])

    print("=" * 64)


if __name__ == "__main__":
    main()
