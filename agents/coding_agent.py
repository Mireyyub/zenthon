"""Coding Agent – sandbox only, stronger offline templates + LLMProvider."""

from __future__ import annotations

from typing import Any, Dict, Optional
import re

from agents.base import BaseAgent, AgentResult
from core.logger import logger

_FORBIDDEN = re.compile(
    r"\b(import|open|exec|eval|__import__|os|sys|subprocess|socket|pathlib|shutil)\b",
    re.I,
)


class CodingAgent(BaseAgent):
    PRODUCTION = True

    def __init__(self, name: str = "CodingAgent", description: str = "Sandbox kod agentı"):
        super().__init__(name=name, description=description)

    def run(self, task: str, context: Optional[Dict[str, Any]] = None) -> AgentResult:
        logger.info(f"CodingAgent: {task[:80]}")
        context = context or {}

        try:
            from tools.registry import tool_registry
            from brain.llm.provider import get_llm_provider
        except Exception as e:
            return AgentResult(success=False, error=str(e))

        provider = get_llm_provider()
        system = (
            "Sən kod generasiya edən agentisən. Yalnız təhlükəsiz Python kodu ver. "
            "Markdown code fence istifadə et. import/os/sys/subprocess yazma."
        )

        code = ""
        llm_used = False
        if provider.is_available:
            comp = provider.complete(
                f"Tapşırıq: {task}\nYalnız kod:",
                system=system,
                temperature=0.2,
                max_tokens=800,
            )
            raw = comp.text if comp.ok else ""
            if raw:
                llm_used = True
                m = re.search(r"```(?:python)?\s*([\s\S]+?)```", raw)
                code = (m.group(1) if m else raw).strip()
                if _FORBIDDEN.search(code):
                    return AgentResult(
                        success=False,
                        error="generated code contains forbidden tokens",
                        metadata={"code": code[:300]},
                    )
            if not code:
                code = self._offline_code(task)
        else:
            code = self._offline_code(task)

        filename = context.get("filename") or "solution.py"
        try:
            write_res = tool_registry.dispatch("write_file", f"{filename}||{code}")
        except Exception as e:
            return AgentResult(
                success=False, error=f"sandbox write failed: {e}", metadata={"code": code}
            )

        run_res = None
        if context.get("run", True):
            try:
                run_res = tool_registry.dispatch("run_python", code)
            except Exception as e:
                run_res = {"error": str(e)}

        return AgentResult(
            success=True,
            output={"code": code, "write": write_res, "run": run_res},
            metadata={
                "sandbox": True,
                "filename": filename,
                "llm_used": llm_used,
                "provider": provider.name,
            },
        )

    def _offline_code(self, task: str) -> str:
        low = task.lower()
        if "faktorial" in low or "factorial" in low:
            return (
                "def factorial(n):\n"
                "    return 1 if n <= 1 else n * factorial(n-1)\n"
                "result = factorial(5)\n"
            )
        if "fibonacci" in low or "fibona" in low:
            return (
                "def fib(n):\n"
                "    a, b = 0, 1\n"
                "    for _ in range(n):\n"
                "        a, b = b, a + b\n"
                "    return a\n"
                "result = fib(10)\n"
            )
        if "cəmi" in low or "sum" in low:
            return "result = sum(range(1, 11))\n"
        if "sort" in low or "sırala" in low:
            return "data = [3, 1, 4, 1, 5]\nresult = sorted(data)\n"
        return f"# offline stub for: {task[:60]}\nresult = None\n"
