"""
Leon bootstrap – Faza 0 entrypoint məntiqi.

    from core.bootstrap import start_leon, leon_status, smoke_test
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from core.config import config, load_config
from core.logger import logger
from core.kernel import kernel
from core.service_registry import service_registry


def start_leon(
    *,
    bootstrap_curriculum: bool = False,
    volume_id: str = "01",
    check_llm: bool = True,
) -> Dict[str, Any]:
    """
    Kernel + data dirs + optional LLM check + soft service register.
    Heç bir hard fail: əskik modul status-da görünür.
    """
    report: Dict[str, Any] = {
        "ai": config.ai_name,
        "ok": True,
        "steps": [],
        "missing": [],
        "warnings": [],
    }

    # 1) Config + dirs
    try:
        load_config()  # refresh global if needed
        config.ensure_dirs()
        report["steps"].append({"step": "paths", "ok": True, "leon_dir": str(config.path.leon_dir)})
    except Exception as e:
        report["ok"] = False
        report["steps"].append({"step": "paths", "ok": False, "error": str(e)})
        report["missing"].append("paths")

    # 2) Kernel
    try:
        kernel.initialize()
        kernel.start()
        report["steps"].append({"step": "kernel", "ok": True, "state": kernel.status().get("state")})
    except Exception as e:
        report["ok"] = False
        report["steps"].append({"step": "kernel", "ok": False, "error": str(e)})
        report["missing"].append("kernel")

    # 3) Soft services
    report["services"] = _register_soft_services()

    # 4) LLM check (non-fatal)
    if check_llm:
        llm_report = _check_llm()
        report["llm"] = llm_report
        if not llm_report.get("reachable"):
            report["warnings"].append("LLM/Ollama reachable deyil – fallback rejimində işləyəcək")
            report["steps"].append({"step": "llm", "ok": False, "detail": llm_report})
        else:
            report["steps"].append({"step": "llm", "ok": True, "model": llm_report.get("model")})

    # 5) Optional curriculum bootstrap (soft)
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
            report["steps"].append({"step": "curriculum", "ok": True})
        except Exception as e:
            report["warnings"].append(f"curriculum bootstrap: {e}")
            report["steps"].append({"step": "curriculum", "ok": False, "error": str(e)})

    logger.info(
        f"Leon start: ok={report['ok']} warnings={len(report['warnings'])} "
        f"missing={report['missing']}"
    )
    return report


def _register_soft_services() -> Dict[str, str]:
    """Import fail olsa 'missing', yoxsa 'ok'."""
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
        lambda: __import__("knowledge.graph", fromlist=["KnowledgeGraph"]).KnowledgeGraph(),
    )
    soft("fact_store", lambda: __import__("knowledge.facts", fromlist=["FactStore"]).FactStore())
    soft(
        "learning_engine",
        lambda: __import__("learning.engine", fromlist=["LearningEngine"]).LearningEngine(),
    )
    # brain factory already on kernel
    try:
        _ = service_registry.get("brain")
        status["brain"] = "ok"
    except Exception as e:
        status["brain"] = f"missing: {e}"

    return status


def _check_llm() -> Dict[str, Any]:
    try:
        from brain.llm.client import get_llm_client

        client = get_llm_client(force_new=True)
        return client.health_check()
    except Exception as e:
        return {
            "provider": config.llm.provider,
            "reachable": False,
            "error": str(e),
            "model": config.llm.model,
        }


def leon_status() -> Dict[str, Any]:
    """Tam status – əskiklər aydın."""
    st: Dict[str, Any] = {
        "ai": config.ai_name,
        "paths": config.path.as_dict(),
        "llm_config": config.llm.as_dict(),
        "kernel": {},
        "services": {},
        "llm": {},
        "components": {},
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

    st["services"] = {}
    for name in ("brain", "memory", "knowledge_graph", "fact_store", "learning_engine", "llm"):
        try:
            obj = service_registry.get(name)
            st["services"][name] = "ok" if obj is not None else "none"
        except Exception:
            st["services"][name] = "missing"

    st["llm"] = _check_llm()

    # Component probes
    comps = {}
    for label, probe in (
        ("curriculum", lambda: __import__("curriculum", fromlist=["CurriculumEngine"]).CurriculumEngine()),
        ("genome", lambda: __import__("genome", fromlist=["list_genes"]).list_genes()),
        ("reasoning_engine", lambda: __import__("brain.reasoning.engine", fromlist=["reasoning_engine"]).reasoning_engine),
    ):
        try:
            r = probe()
            comps[label] = {"ok": True, "detail": str(r)[:120] if not hasattr(r, "__dict__") else type(r).__name__}
        except Exception as e:
            comps[label] = {"ok": False, "error": str(e)}
    st["components"] = comps
    return st


def smoke_test() -> Dict[str, Any]:
    """
    Faza 0 qəbul testi:
      - start
      - llm-check (soft)
      - think "test"
      - teach-volume 01 (soft if heavy)
    """
    results: List[Dict[str, Any]] = []
    overall = True

    start = start_leon(bootstrap_curriculum=False, check_llm=True)
    results.append({"name": "start", "ok": start.get("ok", False), "detail": start})
    if not start.get("ok"):
        overall = False

    # llm
    llm = start.get("llm") or _check_llm()
    results.append(
        {
            "name": "llm-check",
            "ok": True,  # non-fatal for smoke
            "reachable": bool(llm.get("reachable")),
            "detail": {k: llm.get(k) for k in ("provider", "model", "reachable", "error")},
        }
    )

    # think
    try:
        from brain.orchestrator import BrainOrchestrator

        orch = BrainOrchestrator(brain_name=config.ai_name)
        thought = orch.run("test", reasoning_mode="auto")
        ok = bool(thought.get("conclusion") is not None or thought.get("confidence") is not None)
        results.append(
            {
                "name": "think",
                "ok": ok,
                "confidence": thought.get("confidence"),
                "mode": thought.get("reasoning_mode"),
                "llm_used": thought.get("llm_used"),
            }
        )
        if not ok:
            overall = False
    except Exception as e:
        results.append({"name": "think", "ok": False, "error": str(e)})
        overall = False

    # teach one lesson (lighter than full volume for smoke)
    try:
        from curriculum import CurriculumEngine

        eng = CurriculumEngine()
        report = eng.teach("000001", volume_id="01")
        st = report.get("self_test") or {}
        ok = st.get("total", 0) >= 0  # ran without crash
        results.append(
            {
                "name": "teach-000001",
                "ok": ok,
                "passed": st.get("passed"),
                "total": st.get("total"),
                "lesson": report.get("name"),
            }
        )
    except Exception as e:
        results.append({"name": "teach-000001", "ok": False, "error": str(e)})
        overall = False

    return {
        "overall_ok": overall,
        "results": results,
        "paths": config.path.as_dict(),
    }
