"""Safe local LLM reflection bridge for self-improvement."""
from __future__ import annotations

from typing import Any, Dict, Optional

from brain.llm import get_llm_client
from brain.self_improve import self_improve_engine
from learning.engine import learning_engine


def sync_self_learning(topic: str = "general", apply: bool = False) -> Dict[str, Any]:
    """Diagnose local learning gaps, keep LLM reflections pending, then optionally apply safe practice actions."""
    health = get_llm_client(force_new=True).health_check()
    diagnosis = self_improve_engine.run_cycle(apply_changes=False)
    reflection: Optional[str] = None
    if health.get("reachable"):
        prompt = (
            "Yalnız verilən diaqnostikaya əsaslanan qısa öyrənmə planı yaz. "
            "Yeni fakt uydurma. Mövzu: " + topic + "\nDiaqnostika: " + str(diagnosis.get("diagnosis", {}))
        )
        reflection = get_llm_client().complete(prompt, system="Sən təhlükəsiz lokal tədris köməkçisisən.", max_tokens=220)
    learned = learning_engine.learn(
        reflection or f"Öyrənmə diaqnostikası: {diagnosis.get('diagnosis', {})}",
        source="ollama-self-learning",
        confidence=0.4,
        topic=topic,
        llm_reachable=bool(health.get("reachable")),
    )
    applied = self_improve_engine.run_cycle(apply_changes=True, with_mutate=False, with_codegen=False) if apply else None
    return {"ok": True, "llm": health, "diagnosis": diagnosis, "reflection": reflection, "learning": learned, "applied": applied}
