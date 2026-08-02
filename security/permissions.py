"""Permission Manager – icazə idarəsi."""

from __future__ import annotations

from typing import Dict, Set

from core.exceptions import SecurityError
from core.logger import logger


class PermissionManager:
    def __init__(self):
        # role → set of permissions
        self._roles: Dict[str, Set[str]] = {
            "admin": {"*"},
            "user": {"brain.think", "memory.read", "tools.echo", "tools.get_time"},
            "agent": {"brain.think", "memory.read", "memory.write", "tools.*"},
            "guest": {"brain.think"},
        }
        self._user_roles: Dict[str, str] = {"default": "user"}

    def assign_role(self, user: str, role: str) -> None:
        if role not in self._roles:
            raise SecurityError(f"Unknown role: {role}")
        self._user_roles[user] = role

    def check(self, user: str, permission: str) -> bool:
        role = self._user_roles.get(user, "guest")
        perms = self._roles.get(role, set())
        if "*" in perms:
            return True
        if permission in perms:
            return True
        # wildcard prefix (tools.*)
        for p in perms:
            if p.endswith(".*") and permission.startswith(p[:-1]):
                return True
        return False

    def require(self, user: str, permission: str) -> None:
        if not self.check(user, permission):
            logger.warning(f"Permission denied: user={user} perm={permission}")
            raise SecurityError(f"Permission denied: {permission}")
