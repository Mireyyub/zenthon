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
    approved: bool = False,
) -> None:
    """Allowlist, permission, approval and audit boundary before each tool."""
    tool_allowlist.require(name)
    perm = f"tools.{name}"
    permissions.require(user, perm)
    from tools.registry import tool_registry

    tool = tool_registry.get(name)
    if not tool:
        raise KeyError(f"Tool not found: {name}")
    policy = tool.policy
    if policy.requires_confirmation and not approved:
        from core.exceptions import ToolApprovalRequiredError

        audit_log.log(
            "tool.gate",
            user=user,
            details={"tool": name, "risk_level": policy.risk_level, "approved": False, "denied": "approval_required"},
            success=False,
        )
        raise ToolApprovalRequiredError(name)
    # path tools
    if name in ("list_dir", "read_file") and arg:
        sandbox.resolve_path(arg, write=False)
    if name == "write_file":
        path = arg.split("||", 1)[0] if "||" in arg else arg
        if path:
            sandbox.resolve_path(path, write=True)
    audit_log.log(
        "tool.gate",
        user=user,
        details={
            "tool": name,
            "risk_level": policy.risk_level,
            "approved": bool(approved),
            "argument": "[redacted]" if policy.redact_argument and arg else "",
            "argument_length": len(arg),
        },
        success=True,
    )


def safe_tool_call(name: str, arg: str = "", user: str = "agent", approved: bool = False) -> Any:
    from tools.registry import tool_registry

    try:
        result = tool_registry.dispatch(name, arg, user=user, approved=approved)
        audit_log.log("tool.call", user=user, details={"tool": name}, success=True)
        return result
    except Exception as e:
        audit_log.log("tool.call", user=user, details={"tool": name, "error": str(e)}, success=False)
        raise
