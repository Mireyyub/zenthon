"""Security gate – tool call + path (Faza 9)."""

from __future__ import annotations

from typing import Any, Dict, Optional

from security.allowlist import tool_allowlist
from security.audit import audit_log
from security.permissions import permissions
from security.sandbox import sandbox


def gate_tool(
    name: str,
    *,
    user: str = "agent",
    arg: str = "",
) -> None:
    """Allowlist + permission + audit before tool."""
    tool_allowlist.require(name)
    perm = f"tools.{name}"
    permissions.require(user, perm)
    # path tools
    if name in ("list_dir", "read_file") and arg:
        sandbox.resolve_path(arg, write=False)
    if name == "write_file":
        path = arg.split("||", 1)[0] if "||" in arg else arg
        if path:
            sandbox.resolve_path(path, write=True)
    audit_log.log("tool.gate", user=user, details={"tool": name, "arg": arg[:200]}, success=True)


def safe_tool_call(name: str, arg: str = "", user: str = "agent") -> Any:
    from tools.registry import tool_registry

    gate_tool(name, user=user, arg=arg)
    try:
        result = tool_registry.dispatch(name, arg)
        audit_log.log("tool.call", user=user, details={"tool": name}, success=True)
        return result
    except Exception as e:
        audit_log.log("tool.call", user=user, details={"tool": name, "error": str(e)}, success=False)
        raise
