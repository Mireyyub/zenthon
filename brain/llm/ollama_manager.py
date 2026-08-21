"""Local Ollama process and model readiness helpers."""
from __future__ import annotations

import os
import shutil
import subprocess
import time
from typing import Any, Dict

from brain.llm.client import get_llm_client


def ensure_ollama(model: str | None = None, auto_pull: bool | None = None) -> Dict[str, Any]:
    client = get_llm_client(force_new=True)
    target = model or client.config.model
    auto_pull = auto_pull if auto_pull is not None else os.getenv("LEON_OLLAMA_AUTO_PULL", "0") == "1"
    binary = shutil.which("ollama")
    result: Dict[str, Any] = {"binary": bool(binary), "model": target, "started": False, "pulled": False}
    if not binary:
        result["error"] = "Ollama CLI tapılmadı; https://ollama.com/download ilə quraşdırın."
        return result
    health = client.health_check()
    if not health.get("reachable"):
        subprocess.Popen([binary, "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        result["started"] = True
        for _ in range(10):
            time.sleep(0.5)
            health = client.health_check()
            if health.get("reachable"):
                break
    models = health.get("models") or client.list_models()
    if target not in models and auto_pull:
        subprocess.check_call([binary, "pull", target])
        result["pulled"] = True
        health = client.health_check()
    result["health"] = health
    result["ready"] = bool(health.get("reachable")) and target in (health.get("models") or client.list_models())
    return result
