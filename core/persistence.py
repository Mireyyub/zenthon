"""
Leon disk persistence helpers (Faza 1).

JSON / JSONL yaz-oxu – FactStore, Graph, Learning, VectorMemory.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.logger import logger


def _path(p: Path | str) -> Path:
    return Path(p)


def write_json(path: Path | str, data: Any) -> None:
    path = _path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, default=str), encoding="utf-8")


def read_json(path: Path | str, default: Any = None) -> Any:
    path = _path(path)
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        logger.warning(f"read_json failed {path}: {e}")
        return default


def write_jsonl(path: Path | str, rows: List[Dict[str, Any]]) -> None:
    path = _path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")


def append_jsonl(path: Path | str, row: Dict[str, Any]) -> None:
    path = _path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")


def read_jsonl(path: Path | str) -> List[Dict[str, Any]]:
    path = _path(path)
    if not path.exists():
        return []
    rows = []
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except Exception:
                continue
    except Exception as e:
        logger.warning(f"read_jsonl failed {path}: {e}")
    return rows
