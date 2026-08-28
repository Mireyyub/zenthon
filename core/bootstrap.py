"""
Leon bootstrap – paths, kernel, registry services, persist load.
"""

from __future__ import annotations

from typing import Any, Dict, List

from core.config import config, load_config
from core.logger import logger
from core.kernel import kernel
from core.service_registry import service_registry


def start_leon(
    *,
    bootstrap_curriculum: bool = False,
    volume_id: str = "01",
    check_llm: bool = True,
    load_persisted: bool = True,
) -> Dict[str, Any]:
    report: Dict[str, Any] = {
        "ai": config.ai_name,
        "ok": True,
        "steps": [],
        "missing": [],
        "warnings": [],
    }

    try:
        load_config()
        config.ensure_dirs()
        report["steps"].append(
            {"step": "paths", "ok": True, "leon_dir": str(config.path.leon_dir)}
        )
    except Exception as e:
        report["ok"] = False
        report["steps"].append({"step": "paths", "ok": False, "error": str(e)})
        report["missing"].append("paths")

    try:
        kernel.initialize()
        kernel.start()
        report["steps"].append(
            {"step": "kernel", "ok": True, "state": kernel.status().get("state")}
        )
    except Exception as e:
        report["ok"] = False
        report["steps"].append({"step": "kernel", "ok": False, "error": str(e)})
        report["missing"].append("kernel")

    if load_persisted:
        try:
            persisted = load_state()
            report["persisted"] = persisted
            report["steps"].append(
                {"step": "persist_load", "ok": True, "detail": persisted.get("parts")}
            )
        except Exception as e:
            report["warnings"].append(f"persist_load: {e}")
            report["steps"].append({"step": "persist_load", "ok": False, "error": str(e)})

    report["services"] = _register_soft_services()

    if check_llm:
        llm_report = _check_llm()
        report["llm"] = llm_report
        if not llm_report.get("reachable"):
            report["warnings"].append(
                "LLM/Ollama reachable deyil – fallback rejimində işləyəcək"
            )
            report["steps"].append({"step": "llm", "ok": False, "detail": llm_report})
        else:
            report["steps"].append(
                {"step": "llm", "ok": True, "model": llm_report.get("model")}
            )

    if bootstrap_curriculum:
        try:
            from learning import bootstrap_from_specs

            boot = bootstrap_from_specs(volume_id)
            report["curriculum"] = {
                "volume": (boot.get("volume") or {}).get("name"),
                "lessons_passed": (boot.get("volume") or {}).get("lessons_passed"),
                "genes_activated": boot.get("genes_activated"),
                "learning_stats": boot.get("learning_stats"),
            }
            try:
                save_state(name="post_bootstrap")
            except Exception:
                pass
            report["steps"].append({"step": "curriculum", "ok": True})
        except Exception as e:
            report["warnings"].append(f"curriculum bootstrap: {e}")
            report["steps"].append({"step": "curriculum", "ok": False, "error": str(e)})

    logger.info(
        f"Leon start: ok={report['ok']} warnings={len(report['warnings'])} missing={report['missing']}"
    )
    return report


def save_state(name: str = "leon") -> Dict[str, Any]:
    from core.checkpoint import save_leon_state

    return save_leon_state(name=name)


def load_state() -> Dict[str, Any]:
    from core.checkpoint import load_leon_state

    return load_leon_state()


def _register_soft_services() -> Dict[str, str]:
    status: Dict[str, str] = {}

    def soft(name: str, factory):
        try:
            obj = factory()
            service_registry.register(name, obj)
            status[name] = "ok"
        except Exception as e:
            status[name] = f"missing: {type(e).__name__}: {e}"
            logger.debug(f"Service {name} unavailable: {e}")

    soft("memory", lambda: __import__("memory", fromlist=["MemoryManager"]).MemoryManager())
    soft(
        "knowledge_graph",
        lambda: __import__("knowledge.registry", fromlist=["get_graph"]).get_graph(),
    )
    soft(
        "fact_store",
        lambda: __import__("knowledge.registry", fromlist=["get_fact_store"]).get_fact_store(),
    )
    soft(
        "learning_engine",
        lambda: __import__("learning.engine", fromlist=["LearningEngine"]).LearningEngine(),
    )
    soft(
        "reasoning",
        lambda: __import__("brain.reasoning.engine", fromlist=["ReasoningEngine"]).ReasoningEngine(),
    )
    return status


def _check_llm() -> Dict[str, Any]:
    try:
        from brain.llm.provider import get_llm_provider

        return get_llm_provider(force_new=True).health().to_dict()
    except Exception as e:
        return {
            "provider": getattr(config.llm, "provider", "unknown"),
            "reachable": False,
            "error": str(e),
            "model": getattr(config.llm, "model", ""),
        }


def leon_status() -> Dict[str, Any]:
    st: Dict[str, Any] = {
        "ai": config.ai_name,
        "paths": config.path.as_dict(),
        "llm_config": config.llm.as_dict(),
        "kernel": {},
        "services": {},
        "llm": {},
        "components": {},
        "persisted": {},
        "architecture": "ReasoningEngine-primary",
    }
    try:
        if not kernel.status().get("initialized"):
            kernel.initialize()
        st["kernel"] = {
            "initialized": True,
            "state": kernel.status().get("state"),
            "services": kernel.status().get("services"),
        }
    except Exception as e:
        st["kernel"] = {"initialized": False, "error": str(e)}

    for name in (
        "memory",
        "knowledge_graph",
        "fact_store",
        "learning_engine",
        "reasoning",
        "llm",
    ):
        try:
            obj = service_registry.get(name)
            st["services"][name] = "ok" if obj is not None else "none"
        except Exception:
            st["services"][name] = "missing"

    st["llm"] = _check_llm()

    try:
        from knowledge.registry import get_fact_store, get_graph
        from learning.engine import LearningEngine
        from memory.vector_memory import VectorMemory

        st["persisted"] = {
            "facts": len(get_fact_store().all()),
            "graph": get_graph().stats(),
            "learning": LearningEngine().stats(),
            "vector": VectorMemory().count(),
        }
    except Exception as e:
        st["persisted"] = {"error": str(e)}

    comps = {}
    for label, probe in (
        (
            "curriculum",
            lambda: __import__("curriculum", fromlist=["CurriculumEngine"]).CurriculumEngine(),
        ),
        ("genome", lambda: __import__("genome", fromlist=["list_genes"]).list_genes()),
        (
            "reasoning_engine",
            lambda: __import__("brain.reasoning.engine", fromlist=["reasoning_engine"]).reasoning_engine,
        ),
    ):
        try:
            r = probe()
            comps[label] = {
                "ok": True,
                "detail": str(r)[:120] if not hasattr(r, "__dict__") else type(r).__name__,
            }
        except Exception as e:
            comps[label] = {"ok": False, "error": str(e)}
    st["components"] = comps
    return st


def smoke_test() -> Dict[str, Any]:
    results: List[Dict[str, Any]] = []
    overall = True

    start = start_leon(bootstrap_curriculum=False, check_llm=True, load_persisted=True)
    results.append({"name": "start", "ok": start.get("ok", False)})
    if not start.get("ok"):
        overall = False

    llm = start.get("llm") or _check_llm()
    results.append({"name": "llm-check", "ok": True, "reachable": bool(llm.get("reachable"))})

    try:
        from brain.orchestrator import BrainOrchestrator

        orch = BrainOrchestrator(brain_name=config.ai_name)
        thought = orch.run("test", reasoning_mode="auto", use_session=False)
        ok = thought.get("conclusion") is not None or thought.get("confidence") is not None
        results.append(
            {
                "name": "think",
                "ok": ok,
                "confidence": thought.get("confidence"),
                "source": thought.get("source"),
                "path": "ReasoningEngine",
            }
        )
        if not ok:
            overall = False
    except Exception as e:
        results.append({"name": "think", "ok": False, "error": str(e)})
        overall = False

    try:
        from curriculum import CurriculumEngine

        eng = CurriculumEngine()
        report = eng.teach("000001", volume_id="01")
        st = report.get("self_test") or {}
        results.append(
            {
                "name": "teach-000001",
                "ok": True,
                "passed": st.get("passed"),
                "total": st.get("total"),
            }
        )
    except Exception as e:
        results.append({"name": "teach-000001", "ok": False, "error": str(e)})
        overall = False

    try:
        from knowledge.registry import get_fact_store

        marker = f"LEON_PERSIST_MARKER_{__import__('uuid').uuid4().hex[:8]}"
        fs = get_fact_store()
        fs.add(marker, source="smoke", confidence=1.0)
        fs2 = get_fact_store(force_new=True)
        found = any(marker in f.get("statement", "") for f in fs2.all())
        results.append({"name": "persist-facts", "ok": found, "marker": marker})
        if not found:
            overall = False

        save_report = save_state(name="smoke")
        results.append(
            {"name": "save_state", "ok": True, "checkpoint": save_report.get("checkpoint_id")}
        )
    except Exception as e:
        results.append({"name": "persist-facts", "ok": False, "error": str(e)})
        overall = False

    return {
        "overall_ok": overall,
        "results": results,
        "paths": config.path.as_dict(),
        "architecture": "ReasoningEngine-primary",
    }
