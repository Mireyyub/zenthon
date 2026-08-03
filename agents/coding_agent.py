"""
Coding Agent – yalnız sandbox (Faza 5).
Kod generasiyası + optional write/run in data/leon/sandbox.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
import re

from agents.base import BaseAgent, AgentResult
from core.logger import logger


class CodingAgent(BaseAgent):
    PRODUCTION = True

    def __init__(self, name: str = "CodingAgent", description: str = "Sandbox kod agentı"):
        super().__init__(name=name, description=description)

    def run(self, task: str, context: Optional[Dict[str, Any]] = None) -> AgentResult:
        logger.info(f"CodingAgent: {task[:80]}")
        context = context or {}

        try:
            from tools.registry import tool_registry
            from brain.llm.client import get_llm_client
        except Exception as e:
            return AgentResult(success=False, error=str(e))

        client = get_llm_client()
        system = (
            "Sən kod generasiya edən agentisən. Yalnız Python kodu ver. "
            "Markdown code fence istifadə et. Təhlükəli import (os,sys,subprocess) yazma."
        )

        code = ""
        if client.is_available:
            raw = client.complete(
                f"Tapşırıq: {task}\nYalnız kod:",
                system=system,
                temperature=0.2,
                max_tokens=800,
            ) or ""
            m = re.search(r"```(?:python)?\s*([\s\S]+?)```", raw)
            code = (m.group(1) if m else raw).strip()
        else:
            # offline stub for simple factorial-like tasks
            if "faktorial" in task.lower() or "factorial" in task.lower():
                code = (
                    "def factorial(n):\n"
                    "    return 1 if n <= 1 else n * factorial(n-1)\n"
                    "result = factorial(5)\n"
                )
            else:
                code = f"# offline: {task[:80]}\nresult = None\n"

        filename = context.get("filename") or "solution.py"
        # path only under sandbox via tool
        write_res = None
        run_res = None
        try:
            write_res = tool_registry.dispatch("write_file", f"{filename}||{code}")
        except Exception as e:
            return AgentResult(success=False, error=f"sandbox write failed: {e}", metadata={"code": code})

        if context.get("run", True):
            try:
                run_res = tool_registry.dispatch("run_python", code)
            except Exception as e:
                run_res = {"error": str(e)}

        return AgentResult(
            success=True,
            output={
                "code": code,
                "write": write_res,
                "run": run_res,
            },
            metadata={
                "sandbox": True,
                "filename": filename,
                "llm_used": bool(client.is_available),
            },
        )
