"""Filesystem tool – təhlükəsiz fayl əməliyyatları."""

from __future__ import annotations

import os
from pathlib import Path
from typing import List, Optional

from core.logger import logger
from tools.registry import tool_registry

# Təhlükəsizlik: yalnız bu kökdən kənara çıxma
ALLOWED_ROOT = Path.cwd().resolve()


def _safe_path(path: str) -> Path:
    p = (ALLOWED_ROOT / path).resolve()
    if not str(p).startswith(str(ALLOWED_ROOT)):
        raise PermissionError(f"Path outside allowed root: {path}")
    return p


def read_file(path: str) -> str:
    p = _safe_path(path)
    return p.read_text(encoding="utf-8")


def write_file(path: str, content: str) -> str:
    p = _safe_path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return f"Written {len(content)} chars to {path}"


def list_dir(path: str = ".") -> List[str]:
    p = _safe_path(path)
    return sorted([x.name for x in p.iterdir()])


tool_registry.register("read_file", read_file, "Fayl oxu", {"path": "str"})
tool_registry.register("write_file", write_file, "Fayla yaz", {"path": "str", "content": "str"})
tool_registry.register("list_dir", list_dir, "Qovluq siyahısı", {"path": "str"})
