"""Tool Registry – alətlərin qeydiyyatı və çağırılması."""

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


class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, Tool] = {}

    def register(
        self,
        name: str,
        func: Callable,
        description: str = "",
        parameters: Optional[Dict[str, str]] = None,
    ) -> None:
        self._tools[name] = Tool(
            name=name,
            description=description,
            func=func,
            parameters=parameters or {},
        )
        logger.info(f"ToolRegistry: registered '{name}'")

    def get(self, name: str) -> Optional[Tool]:
        return self._tools.get(name)

    def call(self, name: str, **kwargs) -> Any:
        tool = self._tools.get(name)
        if not tool:
            raise KeyError(f"Tool not found: {name}")
        return tool.func(**kwargs)

    def list_tools(self) -> List[Dict[str, str]]:
        return [
            {"name": t.name, "description": t.description}
            for t in self._tools.values()
        ]


tool_registry = ToolRegistry()


# Built-in tools
def _echo(text: str = "") -> str:
    return text


def _get_time() -> str:
    from datetime import datetime
    return datetime.now().isoformat()


tool_registry.register("echo", _echo, "Verilən mətni qaytarır", {"text": "str"})
tool_registry.register("get_time", _get_time, "Cari vaxtı qaytarır")
