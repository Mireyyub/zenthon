"""
Checkpoint – Leon state save/load (Faza 1).
Default dir: data/leon/checkpoints
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from datetime import datetime
from pathlib import Path
import json
import uuid

from core.logger import logger


def _default_dir() -> Path:
    try:
        from core.config import config

        return Path(config.path.checkpoints_dir)
    except Exception:
        return Path("data/leon/checkpoints")


class CheckpointStore:
    def __init__(self, directory: Optional[str | Path] = None):
        self.dir = Path(directory) if directory else _default_dir()
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


def save_leon_state(name: str = "leon") -> Dict[str, Any]:
    """Bütün persist qatlarını diskə flush + checkpoint meta."""
    summary: Dict[str, Any] = {"name": name, "parts": {}}

    try:
        from knowledge.facts import FactStore

        fs = FactStore()
        fs.save()
        summary["parts"]["facts"] = len(fs.all())
    except Exception as e:
        summary["parts"]["facts"] = f"error: {e}"

    try:
        from knowledge.graph import KnowledgeGraph

        kg = KnowledgeGraph()
        kg.save()
        summary["parts"]["graph"] = kg.stats()
    except Exception as e:
        summary["parts"]["graph"] = f"error: {e}"

    try:
        from learning.engine import LearningEngine

        le = LearningEngine()
        le.save()
        summary["parts"]["learning"] = le.stats()
    except Exception as e:
        summary["parts"]["learning"] = f"error: {e}"

    try:
        from memory.vector_memory import VectorMemory

        vm = VectorMemory()
        vm.save()
        summary["parts"]["vector"] = vm.count()
    except Exception as e:
        summary["parts"]["vector"] = f"error: {e}"

    cp_id = checkpoint_store.save(name, {"summary": summary, "saved": True})
    summary["checkpoint_id"] = cp_id
    return summary


def load_leon_state() -> Dict[str, Any]:
    """Diskdən yenidən yüklə (auto_load constructors da edir)."""
    summary: Dict[str, Any] = {"parts": {}}
    try:
        from knowledge.facts import FactStore

        fs = FactStore()
        summary["parts"]["facts"] = fs.load()
    except Exception as e:
        summary["parts"]["facts"] = f"error: {e}"
    try:
        from knowledge.graph import KnowledgeGraph

        kg = KnowledgeGraph()
        summary["parts"]["graph"] = kg.load()
    except Exception as e:
        summary["parts"]["graph"] = f"error: {e}"
    try:
        from learning.engine import LearningEngine

        le = LearningEngine()
        summary["parts"]["learning"] = le.load()
    except Exception as e:
        summary["parts"]["learning"] = f"error: {e}"
    try:
        from memory.vector_memory import VectorMemory

        vm = VectorMemory()
        summary["parts"]["vector"] = vm.load()
    except Exception as e:
        summary["parts"]["vector"] = f"error: {e}"
    return summary
