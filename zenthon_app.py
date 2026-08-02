"""
Zenthon Platform Bootstrap.

İşə salmaq:
    python zenthon_app.py

Ollama ilə:
    ollama serve
    ollama pull llama3.2
    python zenthon_app.py
"""

from core import kernel, event_bus, service_registry, logger
from agents.manager import agent_manager
from tools import tool_registry


def main():
    print("=" * 60)
    print("  Zenthon AI Platform")
    print("=" * 60)

    # 1. Kernel start
    kernel.initialize()
    kernel.start()

    status = kernel.status()
    print(f"\nState     : {status['state']}")
    print(f"Services  : {', '.join(status['services'])}")

    # 2. Brain via registry
    brain = service_registry.get("brain")
    print(f"Brain     : {brain}")

    # 3. Quick think
    print("\n--- Quick Think ---")
    result = brain.think(
        "Zenthon platforması nədir?", 
        goal="Qısa və aydın izah",
        reasoning_mode="auto",
    )
    print(f"Mode       : {result['reasoning_mode']}")
    print(f"Confidence : {result['confidence']}")
    print(f"Decision   : {result['decision']['action']}")
    print(f"Conclusion : {result['conclusion'][:180]}")

    # 4. Agents
    print("\n--- Agents ---")
    print(f"Types: {list(agent_manager._registry.keys())}")
    coder = agent_manager.create("coding", name="DevCoder")
    ar = agent_manager.run(coder.id, "Python-da sadə hello world funksiyası yaz")
    print(f"CodingAgent success={ar.success}")
    if ar.output:
        print(f"  Output: {str(ar.output)[:150]}")

    # 5. Tools
    print("\n--- Tools ---")
    print(f"Available: {[t['name'] for t in tool_registry.list_tools()]}")
    print(f"Time tool: {tool_registry.call('get_time')}")

    # 6. Shutdown
    print("\n--- Shutdown ---")
    kernel.shutdown()
    print("Zenthon stopped.")
    print("=" * 60)


if __name__ == "__main__":
    main()
