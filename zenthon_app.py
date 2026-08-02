"""
Zenthon AI Platform – Full Bootstrap (All Phases).

    python zenthon_app.py
"""

from core import kernel, event_bus, service_registry, logger
from agents.manager import agent_manager
from tools import tool_registry
from memory import MemoryManager
from knowledge import KnowledgeGraph, FactStore, KnowledgeRetrieval
from learning import FeedbackCollector, PerformanceEvaluator, SelfLearning
from security import PermissionManager, AuditLog, Sandbox


def main():
    print("=" * 64)
    print("  Zenthon AI Platform – Full Stack")
    print("=" * 64)

    # ── Phase 1: Core ──
    kernel.initialize()
    kernel.start()
    print(f"\n[Core] State: {kernel.status()['state']}")
    print(f"[Core] Services: {', '.join(kernel.status()['services'])}")

    # ── Phase 2: Brain ──
    brain = service_registry.get("brain")
    print(f"\n[Brain] {brain}")

    # ── Phase 3: Memory ──
    mem = MemoryManager()
    service_registry.register("memory", mem)
    mem.remember("Zenthon modul əsaslı AI platformasıdır", kind="vector")
    mem.remember("Python", kind="semantic", subject="Zenthon", predicate="uses", obj="Python")
    print(f"[Memory] Stats: {mem.stats()}")

    # ── Phase 5: Knowledge ──
    kg = KnowledgeGraph()
    facts = FactStore()
    kr = KnowledgeRetrieval(graph=kg, facts=facts)
    kr.add_knowledge("Zenthon has a ThinkingBrain", entities=["Zenthon", "ThinkingBrain"])
    facts.add("Ollama provides local LLM inference")
    service_registry.register("knowledge", kr)
    print(f"[Knowledge] Graph: {kg.stats()}, Facts: {len(facts.all())}")

    # ── Phase 6: Learning ──
    fb = FeedbackCollector()
    ev = PerformanceEvaluator()
    sl = SelfLearning(feedback=fb, evaluator=ev)
    fb.add("Yaxşı cavab", score=0.8)
    fb.add("Qısa oldu", score=-0.2)
    sl.learn_from_feedback()
    print(f"[Learning] {sl.suggest_improvement()}")

    # ── Phase 4+7: Agents ──
    print(f"\n[Agents] Types: {agent_manager.list_types()}")
    coder = agent_manager.create("coding", name="DevCoder")
    ar = agent_manager.run(coder.id, "Sadə faktorial funksiyası yaz")
    print(f"[Agents] CodingAgent success={ar.success}")

    # ── Phase 8: Security ──
    perms = PermissionManager()
    audit = AuditLog()
    sandbox = Sandbox(timeout_seconds=5)
    service_registry.register("permissions", perms)
    service_registry.register("audit", audit)
    audit.log("platform_start", user="system")
    print(f"[Security] user can brain.think: {perms.check('default', 'brain.think')}")

    # ── Tools ──
    print(f"\n[Tools] { [t['name'] for t in tool_registry.list_tools()] }")

    # ── Integrated Think ──
    print("\n--- Integrated Think ---")
    result = brain.think(
        "Zenthon platformasının əsas üstünlükləri nələrdir?",
        goal="Qısa strukturlaşdırılmış cavab",
        reasoning_mode="auto",
    )
    print(f"Mode       : {result['reasoning_mode']}")
    print(f"Confidence : {result['confidence']}")
    print(f"Decision   : {result['decision']['action']} (risk={result['decision'].get('risk')})")
    print(f"Conclusion : {result['conclusion'][:200]}")

    # ── Recall ──
    recalled = mem.recall("Zenthon")
    print(f"\n[Recall] vector hits: {len(recalled.get('vector', []))}")

    # ── Shutdown ──
    print("\n--- Shutdown ---")
    audit.log("platform_shutdown", user="system")
    kernel.shutdown()
    print("Zenthon stopped cleanly.")
    print("=" * 64)


if __name__ == "__main__":
    main()
