"""Tool Registry – allowlist-aware (Faza 9)."""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass, field

from core.logger import logger


@dataclass
class Tool:
    name: str
    description: str
    func: Callable
    parameters: Dict[str, str] = field(default_factory=dict)
    production: bool = True


class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, Tool] = {}

    def register(
        self,
        name: str,
        func: Callable,
        description: str = "",
        parameters: Optional[Dict[str, str]] = None,
        production: bool = True,
    ) -> None:
        self._tools[name] = Tool(
            name=name,
            description=description,
            func=func,
            parameters=parameters or {},
            production=production,
        )
        logger.info(f"ToolRegistry: registered '{name}'")

    def get(self, name: str) -> Optional[Tool]:
        return self._tools.get(name)

    def call(self, name: str, **kwargs) -> Any:
        tool = self._tools.get(name)
        if not tool:
            raise KeyError(f"Tool not found: {name}")
        return tool.func(**kwargs)

    def dispatch(self, name: str, arg: str = "", *, enforce_security: bool = True) -> Any:
        name = (name or "").strip()
        arg = (arg or "").strip()
        if enforce_security:
            try:
                from security.gate import gate_tool

                gate_tool(name, user="agent", arg=arg)
            except Exception as e:
                # re-raise security errors; soft-skip if security not loaded
                from core.exceptions import SecurityError

                if isinstance(e, SecurityError):
                    raise
                if e.__class__.__name__ == "SecurityError":
                    raise
                # ImportError etc – continue without gate in early boot
                if "SecurityError" in type(e).__name__:
                    raise
                if not isinstance(e, (ImportError, ModuleNotFoundError)):
                    # permission / allowlist raised
                    raise
        tool = self._tools.get(name)
        if not tool:
            raise KeyError(f"Tool not found: {name}")
        params = list(tool.parameters.keys())
        if not params:
            return tool.func()
        key = params[0]
        if key in ("text", "expression", "code", "content"):
            return tool.func(**{key: arg})
        if key == "path":
            return tool.func(path=arg or ".")
        if name == "write_file" and "||" in arg:
            path, content = arg.split("||", 1)
            return tool.func(path=path.strip(), content=content)
        if name == "write_file":
            return tool.func(path=arg, content="")
        return tool.func(**{key: arg})

    def list_tools(self, production_only: bool = False) -> List[Dict[str, str]]:
        out = []
        for t in self._tools.values():
            if production_only and not t.production:
                continue
            out.append(
                {
                    "name": t.name,
                    "description": t.description,
                    "production": str(t.production),
                }
            )
        return out


tool_registry = ToolRegistry()


def _echo(text: str = "") -> str:
    return text


def _get_time() -> str:
    from datetime import datetime

    return datetime.now().isoformat()


def _register_builtins():
    tool_registry.register("echo", _echo, "Verilən mətni qaytarır", {"text": "str"})
    tool_registry.register("get_time", _get_time, "Cari vaxtı qaytarır")
    try:
        from tools.safe_fs import list_dir, read_file, write_file, calc, run_python

        tool_registry.register("list_dir", list_dir, "Sandbox qovluğunu siyahıla", {"path": "str"})
        tool_registry.register("read_file", read_file, "Sandbox faylını oxu", {"path": "str"})
        tool_registry.register(
            "write_file",
            write_file,
            "Sandbox-a yaz (path||content)",
            {"path": "str", "content": "str"},
        )
        tool_registry.register("calc", calc, "Təhlükəsiz riyazi ifadə", {"expression": "str"})
        tool_registry.register("run_python", run_python, "Məhdud Python sandbox", {"code": "str"})
    except Exception as e:
        logger.warning(f"safe_fs tools not loaded: {e}")


_register_builtins()
