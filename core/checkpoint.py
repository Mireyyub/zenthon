"""
Checkpoint – uzun işlərin vəziyyətini saxla / bərpa et.

LangGraph-style sadə persistence.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from datetime import datetime
from pathlib import Path
import json
import uuid

from core.logger import logger


class CheckpointStore:
    def __init__(self, directory: str = ".zenthon_checkpoints"):
        self.dir = Path(directory)
        self.dir.mkdir(parents=True, exist_ok=True)

    def save(self, name: str, state: Dict[str, Any]) -> str:
        cp_id = f"{name}_{uuid.uuid4().hex[:8]}"
        payload = {
            "id": cp_id,
            "name": name,
            "state": state,
            "saved_at": datetime.now().isoformat(),
        }
        path = self.dir / f"{cp_id}.json"
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
        logger.info(f"Checkpoint saved: {cp_id}")
        return cp_id

    def load(self, cp_id: str) -> Optional[Dict[str, Any]]:
        path = self.dir / f"{cp_id}.json"
        if not path.exists():
            # partial match
            matches = list(self.dir.glob(f"{cp_id}*.json"))
            if not matches:
                return None
            path = matches[0]
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return data.get("state")
        except Exception as e:
            logger.error(f"Checkpoint load failed: {e}")
            return None

    def list_checkpoints(self) -> list:
        out = []
        for p in sorted(self.dir.glob("*.json"), reverse=True):
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
                out.append({"id": data.get("id"), "name": data.get("name"), "saved_at": data.get("saved_at")})
            except Exception:
                continue
        return out


checkpoint_store = CheckpointStore()
