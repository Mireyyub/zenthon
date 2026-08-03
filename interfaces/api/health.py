"""Health probe – Ollama + data dir + graph (Faza 7)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict


def health_report() -> Dict[str, Any]:
    report: Dict[str, Any] = {"ok": True, "components": {}}

    # paths
    try:
        from core.config import config

        config.ensure_dirs()
        leon = Path(config.path.leon_dir)
        report["components"]["paths"] = {
            "ok": leon.exists(),
            "leon_dir": str(leon),
            "facts": (leon / "facts").exists(),
            "graph": (leon / "graph").exists(),
        }
        if not leon.exists():
            report["ok"] = False
    except Exception as e:
        report["ok"] = False
        report["components"]["paths"] = {"ok": False, "error": str(e)}

    # llm / ollama
    try:
        from brain.llm.client import get_llm_client

        client = get_llm_client(force_new=True)
        llm = client.health_check()
        report["components"]["llm"] = llm
        # LLM offline is soft – system still ok
        report["components"]["llm"]["soft"] = not bool(llm.get("reachable"))
    except Exception as e:
        report["components"]["llm"] = {"reachable": False, "error": str(e), "soft": True}

    # graph / facts stats
    try:
        from knowledge.graph import KnowledgeGraph
        from knowledge.facts import FactStore

        kg = KnowledgeGraph()
        fs = FactStore()
        report["components"]["knowledge"] = {
            "ok": True,
            "graph": kg.stats(),
            "facts": len(fs.all()),
        }
    except Exception as e:
        report["components"]["knowledge"] = {"ok": False, "error": str(e)}
        report["ok"] = False

    # learning
    try:
        from learning.engine import LearningEngine

        le = LearningEngine()
        report["components"]["learning"] = {"ok": True, **le.stats()}
    except Exception as e:
        report["components"]["learning"] = {"ok": False, "error": str(e)}

    return report
