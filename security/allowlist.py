"""Tool allowlist (Faza 9)."""

from __future__ import annotations

from typing import Dict, FrozenSet, Set

# Production-safe tools only by default
DEFAULT_ALLOWED: FrozenSet[str] = frozenset(
    {
        "echo",
        "get_time",
        "list_dir",
        "read_file",
        "write_file",
        "calc",
        "run_python",
    }
)

# Always denied even if someone tries to register
DENIED: FrozenSet[str] = frozenset(
    {
        "shell",
        "bash",
        "exec",
        "system",
        "subprocess",
        "eval",
        "network",
        "http",
        "fetch",
        "download",
    }
)


class ToolAllowlist:
    def __init__(self, allowed: Set[str] | None = None):
        self._allowed: Set[str] = set(allowed) if allowed is not None else set(DEFAULT_ALLOWED)

    def allow(self, name: str) -> None:
        if name in DENIED:
            raise ValueError(f"tool permanently denied: {name}")
        self._allowed.add(name)

    def deny(self, name: str) -> None:
        self._allowed.discard(name)

    def is_allowed(self, name: str) -> bool:
        if name in DENIED:
            return False
        return name in self._allowed

    def require(self, name: str) -> None:
        from core.exceptions import SecurityError

        if not self.is_allowed(name):
            raise SecurityError(f"Tool not allowlisted: {name}")

    def list_allowed(self) -> list:
        return sorted(self._allowed)


tool_allowlist = ToolAllowlist()
