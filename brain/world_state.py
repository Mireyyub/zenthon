"""
Minimal world state for long-horizon planning.
Tracks facts about the environment Leon believes hold now.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.persistence import write_json, read_json


def _path() -> Path:
    try:
        from core.config import config

        d = Path(config.path.leon_dir) / "world"
    except Exception:
        d = Path("data/leon/world")
    d.mkdir(parents=True, exist_ok=True)
    return d / "state.json"


class WorldState:
    def __init__(self):
        self._data: Dict[str, Any] = read_json(
            _path(),
            default={
                "entities": {},
                "flags": {},
                "history": [],
                "updated_at": None,
            },
        ) or {"entities": {}, "flags": {}, "history": [], "updated_at": None}

    def get(self, key: str, default: Any = None) -> Any:
        if key in (self._data.get("flags") or {}):
            return self._data["flags"][key]
        return (self._data.get("entities") or {}).get(key, default)

    def set_flag(self, key: str, value: Any, *, note: str = "") -> None:
        self._data.setdefault("flags", {})[key] = value
        self._hist("flag", key, value, note)
        self._save()

    def set_entity(self, name: str, props: Dict[str, Any], *, note: str = "") -> None:
        ents = self._data.setdefault("entities", {})
        cur = dict(ents.get(name) or {})
        cur.update(props)
        ents[name] = cur
        self._hist("entity", name, props, note)
        self._save()

    def snapshot(self) -> Dict[str, Any]:
        return {
            "entities": dict(self._data.get("entities") or {}),
            "flags": dict(self._data.get("flags") or {}),
            "updated_at": self._data.get("updated_at"),
            "history_len": len(self._data.get("history") or []),
        }

    def apply_outcome(self, action: str, result: Any) -> None:
        self.set_flag(f"last_action", action, note="outcome")
        self.set_flag(f"last_ok", not bool(isinstance(result, dict) and result.get("error")))
        if isinstance(result, dict) and result.get("pass_rate") is not None:
            self.set_flag("last_pass_rate", result.get("pass_rate"))

    def _hist(self, kind: str, key: str, value: Any, note: str) -> None:
        h = self._data.setdefault("history", [])
        h.append(
            {
                "at": datetime.now().isoformat(),
                "kind": kind,
                "key": key,
                "value": value if not isinstance(value, dict) else {k: value[k] for k in list(value)[:8]},
                "note": note,
            }
        )
        self._data["history"] = h[-200:]

    def _save(self) -> None:
        self._data["updated_at"] = datetime.now().isoformat()
        write_json(_path(), self._data)


world_state = WorldState()
