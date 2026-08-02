"""
Community-pattern agents demo: ReAct, PEV, Crew.

    python -m brain.examples.demo_agents
"""

from agents.manager import agent_manager
from agents.crew import default_research_crew


def main():
    print("=" * 60)
    print("Zenthon – Community Agent Patterns Demo")
    print("=" * 60)
    print(f"Agent types: {agent_manager.list_types()}")

    # ReAct
    print("\n--- ReAct ---")
    if "react" in agent_manager.list_types():
        a = agent_manager.create("react")
        r = agent_manager.run(a.id, "Cari vaxtı öyrən və echo ilə təsdiqlə")
        print(f"Success: {r.success}")
        print(f"Output : {str(r.output)[:200]}")
        print(f"Meta   : {r.metadata}")

    # PEV
    print("\n--- Plan-Execute-Verify ---")
    if "pev" in agent_manager.list_types():
        a = agent_manager.create("pev")
        r = agent_manager.run(a.id, "Kiçik TODO list CLI proqramı üçün plan")
        print(f"Success: {r.success}")
        if isinstance(r.output, dict):
            print(f"Plan   : {str(r.output.get('plan'))[:150]}")
            print(f"Verify : {str(r.output.get('verification'))[:150]}")

    # Crew
    print("\n--- Multi-Agent Crew ---")
    crew = default_research_crew("lokal RAG sistemi")
    cr = crew.run(overall_goal="Minimal işlək RAG prototipi")
    print(f"Crew success: {cr.success}")
    for o in cr.outputs:
        print(f"  [{o['agent']}] ok={o['success']} → {str(o['output'])[:100]}")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
