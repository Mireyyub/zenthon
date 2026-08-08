"""
tools/engine.py — Tool calling engine from zenthon_v10, adapted for zenthon.
Coexists with tools/registry.py; use this for OpenAI-style function schemas.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from core.logger import logger


class ToolError(Exception):
    pass


@dataclass
class ToolDefinition:
    name: str
    description: str
    parameters: Dict[str, Any]
    func: Callable
    returns: str = "string"
    async_func: bool = False
    dangerous: bool = False


@dataclass
class ToolCall:
    tool_name: str
    arguments: Dict[str, Any]
    call_id: str = field(
        default_factory=lambda: "call_" + datetime.now().strftime("%H%M%S")
    )


@dataclass
class ToolResult:
    call_id: str
    tool_name: str
    success: bool
    result: Any
    error: Optional[str] = None
    latency_ms: float = 0.0


class ToolEngine:
    """Registry + dispatch with security awareness."""

    def __init__(self) -> None:
        self._tools: Dict[str, ToolDefinition] = {}
        self._register_builtins()

    def register(self, tool_def: ToolDefinition) -> None:
        self._tools[tool_def.name] = tool_def
        logger.info(f"[ToolEngine] registered: {tool_def.name}")

    def get(self, name: str) -> Optional[ToolDefinition]:
        return self._tools.get(name)

    def list_openai_schema(self) -> List[Dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.parameters,
                },
            }
            for t in self._tools.values()
            if not t.dangerous
        ]

    def descriptions_text(self) -> str:
        lines = ["Mövcud alətlər:"]
        for t in self._tools.values():
            risk = " [dangerous]" if t.dangerous else ""
            lines.append(f"  - {t.name}: {t.description}{risk}")
        return "\n".join(lines)

    def call(self, name: str, arguments: Optional[Dict[str, Any]] = None) -> ToolResult:
        arguments = arguments or {}
        call_id = "call_" + datetime.now().strftime("%H%M%S")
        t0 = time.time()
        tool = self.get(name)
        if not tool:
            return ToolResult(call_id, name, False, None, error=f"unknown tool: {name}")
        if tool.dangerous:
            try:
                from security.gate import check_tool_allowed
                if not check_tool_allowed(name):
                    return ToolResult(
                        call_id, name, False, None,
                        error="blocked by security gate",
                        latency_ms=(time.time() - t0) * 1000,
                    )
            except Exception:
                return ToolResult(
                    call_id, name, False, None,
                    error="dangerous tool requires security gate",
                    latency_ms=(time.time() - t0) * 1000,
                )
        try:
            result = tool.func(**arguments) if arguments else tool.func()
            return ToolResult(
                call_id, name, True, result,
                latency_ms=(time.time() - t0) * 1000,
            )
        except Exception as e:
            return ToolResult(
                call_id, name, False, None,
                error=str(e),
                latency_ms=(time.time() - t0) * 1000,
            )

    def _register_builtins(self) -> None:
        def _calc(expression: str = "0") -> Any:
            from tools.domain.math_ops import safe_eval_math
            return safe_eval_math(expression)

        def _element(symbol: str = "H") -> Any:
            from tools.domain.chemistry import periodic_lookup
            return periodic_lookup(symbol)

        def _skill(name: str = "help", args: str = "") -> Any:
            from agents.skills.registry import get_skill_registry
            return get_skill_registry().run(name, args).to_dict()

        self.register(ToolDefinition(
            name="calc",
            description="Təhlükəsiz riyazi ifadə hesabla",
            parameters={
                "type": "object",
                "properties": {"expression": {"type": "string"}},
                "required": ["expression"],
            },
            func=_calc,
        ))
        self.register(ToolDefinition(
            name="periodic_element",
            description="Periodik cədvəldən element axtar",
            parameters={
                "type": "object",
                "properties": {"symbol": {"type": "string"}},
                "required": ["symbol"],
            },
            func=_element,
        ))
        self.register(ToolDefinition(
            name="run_skill",
            description="Skill registry-dən skill işə sal",
            parameters={
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "args": {"type": "string"},
                },
                "required": ["name"],
            },
            func=_skill,
        ))


_engine: Optional[ToolEngine] = None


def get_tool_engine() -> ToolEngine:
    global _engine
    if _engine is None:
        _engine = ToolEngine()
    return _engine
