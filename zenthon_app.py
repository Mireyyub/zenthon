"""
Leon AI Platform – Full Bootstrap.

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
    print("  Leon AI Platform – Full Stack")
    print("=" * 64)

    kernel.initialize()
    kernel.start()
    print(f"\n[Core] State: {kernel.status()['state']}")
    print(f"[Core] Services: {', '.join(kernel.status()['services'])}")

    brain = service_registry.get("brain")
    print(f"\n[Brain] {brain}")

    mem = MemoryManager()
    service_registry.register("memory", mem)
    mem.remember("Leon modul əsaslı AI platformasıdır", kind="vector")
    mem.remember("Python", kind="semantic", subject="Leon", predicate="uses", obj="Python")
    print(f"[Memory] Stats: {mem.stats()}")

    kg = KnowledgeGraph()
    facts = FactStore()
    kr = KnowledgeRetrieval(graph=kg, facts=facts)
    kr.add_knowledge("Leon has a ThinkingBrain", entities=["Leon", "ThinkingBrain"])
    facts.add("Ollama provides local LLM inference")
    service_registry.register("knowledge", kr)
    print(f"[Knowledge] Graph: {kg.stats()}, Facts: {len(facts.all())}")

    fb = FeedbackCollector()
    ev = PerformanceEvaluator()
    sl = SelfLearning(feedback=fb, evaluator=ev)
    fb.add("Yaxşı cavab", score=0.8)
    fb.add("Qısa oldu", score=-0.2)
    sl.learn_from_feedback()
    print(f"[Learning] {sl.suggest_improvement()}")

    print(f"\n[Agents] Types: {agent_manager.list_types()}")
    coder = agent_manager.create("coding", name="DevCoder")
    ar = agent_manager.run(coder.id, "Sadə faktorial funksiyası yaz")
    print(f"[Agents] CodingAgent success={ar.success}")

    perms = PermissionManager()
    audit = AuditLog()
    service_registry.register("permissions", perms)
    service_registry.register("audit", audit)
    audit.log("platform_start", user="system")
    print(f"[Security] user can brain.think: {perms.check('default', 'brain.think')}")

    print(f"\n[Tools] {[t['name'] for t in tool_registry.list_tools()]}")

    print("\n--- Integrated Think (Leon) ---")
    result = brain.think(
        "Leon platformasının əsas üstünlükləri nələrdir?",
        goal="Qısa strukturlaşdırılmış cavab",
        reasoning_mode="auto",
    )
    print(f"Mode       : {result['reasoning_mode']}")
    print(f"Confidence : {result['confidence']}")
    print(f"Decision   : {result['decision']['action']} (risk={result['decision'].get('risk')})")
    print(f"Conclusion : {result['conclusion'][:200]}")

    recalled = mem.recall("Leon")
    print(f"\n[Recall] vector hits: {len(recalled.get('vector', []))}")

    print("\n--- Shutdown ---")
    audit.log("platform_shutdown", user="system")
    kernel.shutdown()
    print("Leon stopped cleanly.")
    print("=" * 64)


if __name__ == "__main__":
    main()
