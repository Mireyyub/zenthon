"""Audit Log – əməliyyat jurnalı."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from datetime import datetime
import uuid


class AuditLog:
    def __init__(self, max_entries: int = 5000):
        self._entries: List[Dict[str, Any]] = []
        self.max_entries = max_entries

    def log(
        self,
        action: str,
        user: str = "system",
        details: Optional[Dict] = None,
        success: bool = True,
    ) -> str:
        entry_id = str(uuid.uuid4())[:10]
        self._entries.append({
            "id": entry_id,
            "action": action,
            "user": user,
            "details": details or {},
            "success": success,
            "timestamp": datetime.now().isoformat(),
        })
        if len(self._entries) > self.max_entries:
            self._entries = self._entries[-self.max_entries :]
        return entry_id

    def query(
        self,
        user: Optional[str] = None,
        action: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict]:
        results = self._entries
        if user:
            results = [e for e in results if e["user"] == user]
        if action:
            results = [e for e in results if action in e["action"]]
        return results[-limit:]

    def clear(self) -> None:
        self._entries.clear()
