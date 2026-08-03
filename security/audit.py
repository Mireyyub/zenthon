"""Audit log – memory + disk JSONL (Faza 9)."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
import json
import uuid


def _audit_path() -> Path:
    try:
        from core.config import config

        d = Path(config.path.leon_dir) / "audit"
    except Exception:
        d = Path("data/leon/audit")
    d.mkdir(parents=True, exist_ok=True)
    return d / "audit.jsonl"


class AuditLog:
    def __init__(self, max_entries: int = 5000, persist: bool = True):
        self._entries: List[Dict[str, Any]] = []
        self.max_entries = max_entries
        self.persist = persist

    def log(
        self,
        action: str,
        user: str = "system",
        details: Optional[Dict] = None,
        success: bool = True,
    ) -> str:
        entry_id = str(uuid.uuid4())[:10]
        entry = {
            "id": entry_id,
            "action": action,
            "user": user,
            "details": details or {},
            "success": success,
            "timestamp": datetime.now().isoformat(),
        }
        self._entries.append(entry)
        if len(self._entries) > self.max_entries:
            self._entries = self._entries[-self.max_entries :]
        if self.persist:
            try:
                with open(_audit_path(), "a", encoding="utf-8") as f:
                    f.write(json.dumps(entry, ensure_ascii=False, default=str) + "\n")
            except Exception:
                pass
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

    def tail_disk(self, limit: int = 50) -> List[Dict]:
        path = _audit_path()
        if not path.exists():
            return []
        lines = path.read_text(encoding="utf-8").splitlines()
        out = []
        for line in lines[-limit:]:
            try:
                out.append(json.loads(line))
            except Exception:
                continue
        return out

    def clear(self) -> None:
        self._entries.clear()


audit_log = AuditLog()
