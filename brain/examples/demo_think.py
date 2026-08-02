"""
ThinkingBrain – gücləndirilmiş demo.

İşə salmaq (repo kökündən):
    python -m brain.examples.demo_think
"""

from brain import ThinkingBrain


def main():
    brain = ThinkingBrain(name="DemoBrain", enable_meta=True)

    print("=" * 64)
    print("Zenthon ThinkingBrain – Gücləndirilmiş Demo")
    print("=" * 64)

    # 1. Sadə sual
    print("\n[1] Sadə sual (auto)")
    r1 = brain.think("Süni intellekt nədir?", reasoning_mode="auto")
    _print_result(r1)

    # 2. Müqayisə (auto → tot)
    print("\n[2] Müqayisə sualı (auto)")
    r2 = brain.think(
        "CNN və Transformer hansı hallarda daha yaxşıdır? Müqayisə et və seç.",
        goal="Düzgün arxitektura seçimi",
        reasoning_mode="auto",
    )
    _print_result(r2)

    # 3. Plan (auto → sot)
    print("\n[3] Plan sualı (auto)")
    r3 = brain.think(
        "Multimodal AI sistemi qurmaq üçün addım-addım plan və struktur hazırla.",
        goal="İşlək və genişlənə bilən arxitektura",
        reasoning_mode="auto",
    )
    _print_result(r3)
    print("Trace (son addımlar):")
    for step in r3["trace"][-5:]:
        print(f"  • {step[:110]}")

    # 4. Aşağı etimad simulyasiyası + rethink
    print("\n[4] Məqsəd + yaddaş + vəziyyət")
    plan = brain.set_goal("Zenthon-u production-ready etmək")
    print("Plan:")
    for p in plan[:5]:
        print(f"  {p}")

    brain.remember("preferred_stack", "PyTorch + FastAPI", metadata={"importance": 0.9})
    brain.remember("team_size", "kiçik komanda", importance=0.7)
    print("Recall:", brain.recall("preferred"))

    state = brain.get_state()
    print(f"\nCycles       : {state['cycle_count']}")
    print(f"Goal         : {state['current_goal']}")
    print(f"Uncertainty  : {state['uncertainty']}")
    print(f"WM size      : {state['working_memory_size']}")
    if state.get("recent_reflections"):
        print(f"Last reflect : {state['recent_reflections'][-1][:90]}")

    print("\n" + "=" * 64)
    print("Demo bitdi.")
    print("=" * 64)


def _print_result(r: dict):
    print(f"  Mode        : {r['reasoning_mode']} (tried: {r.get('modes_tried')})")
    print(f"  Confidence  : {r['confidence']}  |  Uncertainty: {r.get('uncertainty')}")
    print(f"  Decision    : {r['decision']['action']} (risk={r['decision'].get('risk')})")
    print(f"  Composite   : {r['decision'].get('composite_score')}")
    print(f"  Conclusion  : {r['conclusion'][:130]}...")
    if r.get("meta_reflection"):
        print(f"  Reflection  : {r['meta_reflection'][:100]}")


if __name__ == "__main__":
    main()
