"""
Dərin agentic demo: session, reflexion, checkpoint, HITL.

    python -m brain.examples.demo_deep
"""

from brain.orchestrator import BrainOrchestrator
from agents.manager import agent_manager


def main():
    print("=" * 60)
    print("Zenthon Deep Agentic Demo")
    print("=" * 60)

    orch = BrainOrchestrator()

    # HITL: avtomatik qəbul (demo)
    orch.set_hitl(lambda result: float(result.get("confidence") or 0) >= 0.4)

    # Multi-turn session
    print("\n--- Session turn 1 ---")
    r1 = orch.run("Mən lokal RAG sistemi qurmaq istəyirəm", goal="Aydın plan", archive_result=True)
    print(f"Conf={r1['confidence']} | {str(r1.get('conclusion'))[:120]}")

    print("\n--- Session turn 2 ---")
    r2 = orch.run("Hansı embedding modeli uyğundur?", checkpoint_name="rag_chat")
    print(f"Conf={r2['confidence']} | checkpoint={r2.get('checkpoint_id')}")
    print(f"Session turns: {len(orch.session.turns)}")

    # Reflexion
    print("\n--- Reflexion ---")
    if "reflexion" in agent_manager.list_types():
        a = agent_manager.create("reflexion")
        rr = agent_manager.run(a.id, "2 cümlə ilə RAG izah et", context={"max_retries": 1})
        print(f"Attempts: {rr.metadata.get('attempts')}")
        print(f"Output: {str(rr.output)[:150]}")

    print("\n--- Status ---")
    st = orch.status()
    print(f"Archival: {st['archival_count']} | Session: {st['session_turns']}")

    print("=" * 60)


if __name__ == "__main__":
    main()
