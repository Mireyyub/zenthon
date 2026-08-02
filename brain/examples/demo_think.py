"""
ThinkingBrain demo – sadə istifadə nümunəsi.

İşə salmaq üçün (repo kökündən):
    python -m brain.examples.demo_think
"""

from brain import ThinkingBrain


def main():
    brain = ThinkingBrain(name="DemoBrain")

    print("=" * 60)
    print("Zenthon ThinkingBrain Demo")
    print("=" * 60)

    # 1. Sadə sual (auto → cot gözlənilir)
    print("\n[1] Sadə sual (auto mode)")
    r1 = brain.think(
        "Süni intellekt nədir?",
        reasoning_mode="auto",
    )
    print(f"Mode     : {r1['reasoning_mode']}")
    print(f"Confidence: {r1['confidence']}")
    print(f"Conclusion: {r1['conclusion'][:120]}...")
    print(f"Decision  : {r1['decision']['action']} → {r1['decision']['message']}")

    # 2. Müqayisə sualı (auto → tot gözlənilir)
    print("\n[2] Müqayisə sualı (auto mode)")
    r2 = brain.think(
        "CNN və Transformer hansı hallarda daha yaxşıdır? Müqayisə et.",
        goal="Düzgün seçim etmək",
        reasoning_mode="auto",
    )
    print(f"Mode     : {r2['reasoning_mode']}")
    print(f"Confidence: {r2['confidence']}")
    print(f"Conclusion: {r2['conclusion'][:120]}...")

    # 3. Plan tələb edən sual (auto → sot gözlənilir)
    print("\n[3] Plan / struktur sualı (auto mode)")
    r3 = brain.think(
        "Multimodal AI sistemi qurmaq üçün addım-addım plan hazırla.",
        goal="İşlək arxitektura çıxarmaq",
        reasoning_mode="auto",
    )
    print(f"Mode     : {r3['reasoning_mode']}")
    print(f"Confidence: {r3['confidence']}")
    print("Trace (son 4 addım):")
    for step in r3["trace"][-4:]:
        print(f"  • {step[:100]}")

    # 4. Məqsəd + yaddaş
    print("\n[4] Məqsəd təyin et + yaddaşa yaz")
    plan = brain.set_goal("Zenthon-u production-a çıxarmaq")
    print("Plan:")
    for p in plan:
        print(f"  {p}")

    brain.remember("prefer_mode", "sot", metadata={"reason": "struktur lazımdır"})
    recalled = brain.recall("prefer")
    print(f"Yaddaşdan oxunan: {recalled}")

    # 5. Vəziyyət
    print("\n[5] Beyin vəziyyəti")
    state = brain.get_state()
    print(f"Cycles          : {state['cycle_count']}")
    print(f"Current goal    : {state['current_goal']}")
    print(f"Working memory  : {state['working_memory_size']}")
    print(f"Last decision   : {state['last_decision']['action'] if state['last_decision'] else None}")

    print("\n" + "=" * 60)
    print("Demo bitdi.")
    print("=" * 60)


if __name__ == "__main__":
    main()
