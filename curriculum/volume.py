"""
Genesis Curriculum – Volume idarəetməsi.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Optional

VOLUMES_DIR = Path(__file__).resolve().parent / "volumes"


def list_volumes() -> List[str]:
    if not VOLUMES_DIR.exists():
        return []
    return sorted([p.name for p in VOLUMES_DIR.iterdir() if p.is_dir()])


def load_volume(volume_id: str = "01") -> Dict[str, Any]:
    path = _resolve_volume_dir(volume_id)
    if path is None:
        raise FileNotFoundError(f"Volume not found: {volume_id}")

    meta_path = path / "VOLUME.md"
    text = meta_path.read_text(encoding="utf-8") if meta_path.exists() else ""
    meta = _parse_volume_meta(text)
    meta["path"] = str(path)
    meta["lessons"] = _list_volume_lessons(path)
    return meta


def _resolve_volume_dir(volume_id: str) -> Optional[Path]:
    if not VOLUMES_DIR.exists():
        return None
    # 01 or 01_foundation
    for p in VOLUMES_DIR.iterdir():
        if not p.is_dir():
            continue
        if p.name == volume_id or p.name.startswith(volume_id):
            return p
    return None


def _list_volume_lessons(volume_dir: Path) -> List[str]:
    lessons_dir = volume_dir / "lessons"
    if not lessons_dir.exists():
        return []
    ids = []
    for p in sorted(lessons_dir.glob("*.md")):
        m = re.match(r"(\d+)", p.stem)
        if m:
            ids.append(m.group(1))
    return ids


def _parse_volume_meta(text: str) -> Dict[str, Any]:
    data: Dict[str, Any] = {
        "volume": "",
        "name": "",
        "version": "1.0.0",
        "purpose": "",
        "target_concepts": [],
        "raw": text,
    }
    for line in text.splitlines():
        if line.startswith("Volume:"):
            data["volume"] = line.split(":", 1)[1].strip()
        elif line.startswith("Name:"):
            data["name"] = line.split(":", 1)[1].strip()
        elif line.startswith("Version:"):
            data["version"] = line.split(":", 1)[1].strip()

    # Purpose section
    parts = re.split(r"\n-{5,}\n", text)
    for sec in parts:
        lines = sec.strip().splitlines()
        if not lines:
            continue
        header = lines[0].strip().lower()
        body = "\n".join(lines[1:]).strip()
        if header == "purpose":
            data["purpose"] = body
            # extract bullet concepts
            concepts = []
            for ln in body.splitlines():
                ln = ln.strip()
                if ln.startswith("-"):
                    concepts.append(ln.lstrip("- ").strip())
            data["target_concepts"] = concepts
    return data


def get_lesson_path(lesson_id: str, volume_id: Optional[str] = None) -> Optional[Path]:
    """Dərs faylını volume içində və ya köhnə lessons/ qovluğunda tap."""
    if volume_id:
        vdir = _resolve_volume_dir(volume_id)
        if vdir:
            for p in (vdir / "lessons").glob(f"{lesson_id}*.md"):
                return p
    # search all volumes
    if VOLUMES_DIR.exists():
        for vdir in sorted(VOLUMES_DIR.iterdir()):
            lessons = vdir / "lessons"
            if not lessons.exists():
                continue
            for p in lessons.glob(f"{lesson_id}*.md"):
                return p
    # legacy flat lessons/
    legacy = Path(__file__).resolve().parent / "lessons"
    if legacy.exists():
        for p in legacy.glob(f"{lesson_id}*.md"):
            return p
    return None
