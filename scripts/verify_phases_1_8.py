#!/usr/bin/env python3
"""Verify Leon phases 1–8 acceptance (aurora-dev-cortex + leon-omniverse)."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def step(name: str, fn) -> Dict[str, Any]:
    try:
        detail = fn()
        return {"phase_check": name, "ok": True, "detail": detail}
    except Exception as e:
        return {"phase_check": name, "ok": False, "error": str(e)}


def main() -> int:
    results: List[Dict[str, Any]] = []

    def p1():
        from knowledge.registry import get_fact_store, get_graph, reload_all

        fs = get_fact_store()
        fid = fs.add("VERIFY_PHASE1_FACT", source="verify", confidence=1.0)
        fs2 = get_fact_store(force_new=True)
        found = any("VERIFY_PHASE1_FACT" in f.get("statement", "") for f in fs2.all())
        kg = get_graph()
        a = kg.add_node("verify_node_a")
        b = kg.add_node("verify_node_b")
        kg.add_edge(a, b, "related_to")
        integ = kg.validate_integrity()
        return {"fact_id": fid, "persist_ok": found, "graph": kg.stats(), "integrity": integ}

    def p2():
        from curriculum import CurriculumEngine

        eng = CurriculumEngine()
        r = eng.teach("000001", volume_id="01")
        st = r.get("self_test") or {}
        return {"lesson": r.get("name"), "self_test": st}

    def p3():
        from brain.reasoning.engine import ReasoningEngine

        re = ReasoningEngine(persist_traces=True)
        out = re.reason("Daş mövcuddurmu?", use_brain=False)
        assert "trace_id" in out
        assert "confidence" in out
        return {
            "answer": out.get("answer"),
            "source": out.get("source"),
            "trace_id": out.get("trace_id"),
        }

    def p4():
        from memory.retrieve import retrieve
        from learning.engine import LearningEngine

        le = LearningEngine()
        rec = le.observe("VERIFY validated claim about objects", source="verify", confidence=0.95)
        ret = retrieve("obyekt", top_k=3)
        return {"learning_status": rec.status, "retrieve_keys": list(ret.keys())}

    def p5():
        from agents.manager import agent_manager
        from tools.registry import tool_registry

        types = agent_manager.list_types_detailed()
        prod = [t for t in types if t.get("production")]
        tools = tool_registry.list_tools(production_only=True)
        # offline react heuristic
        agent = agent_manager.create("react")
        res = agent_manager.run(agent.id, "vaxt neçədir?")
        return {"prod_agents": prod, "tools": len(tools), "react_ok": res.success}

    def p6():
        from brain.planning import curriculum_learn_plan, Planner

        plan = curriculum_learn_plan("01")
        ordered = Planner().ordered_tasks(plan)
        return {"plan_id": plan.id, "tasks": len(ordered), "status": plan.status}

    def p7():
        from interfaces.api.health import health_report

        h = health_report()
        return {"health_ok": h.get("ok"), "components": list((h.get("components") or {}).keys())}

    def p8():
        from integrations.omniverse import OmniverseBridge

        ov = OmniverseBridge()
        ov.load_stub_demo_scene()
        st = ov.status()
        return {"mode": st.get("mode"), "objects": st.get("objects")}

    results.append(step("1_persist", p1))
    results.append(step("2_curriculum", p2))
    results.append(step("3_reasoning", p3))
    results.append(step("4_memory_learning", p4))
    results.append(step("5_agents_tools", p5))
    results.append(step("6_planner", p6))
    results.append(step("7_health_api", p7))
    results.append(step("8_omniverse_stub", p8))

    overall = all(r.get("ok") for r in results)
    out = {"overall_ok": overall, "results": results}
    print(json.dumps(out, ensure_ascii=False, indent=2, default=str))
    return 0 if overall else 1


if __name__ == "__main__":
    sys.exit(main())
