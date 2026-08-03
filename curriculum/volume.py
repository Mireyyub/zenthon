"""Genesis Curriculum – Volume idarəetməsi."""

from __future__ import annotations

import json
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

    meta: Dict[str, Any] = {
        "volume": volume_id,
        "name": "",
        "version": "1.0.0",
        "purpose": "",
        "target_concepts": [],
        "lessons": [],
        "path": str(path),
        "raw": "",
    }

    # Prefer index.json
    index_path = path / "index.json"
    if index_path.exists():
        try:
            idx = json.loads(index_path.read_text(encoding="utf-8"))
            meta["volume"] = str(idx.get("volume", volume_id))
            meta["name"] = idx.get("title") or idx.get("name") or ""
            meta["version"] = idx.get("version", meta["version"])
            meta["lessons"] = [str(x) for x in (idx.get("lessons") or [])]
            meta["target_concepts"] = idx.get("target_concepts") or []
        except Exception:
            pass

    meta_path = path / "VOLUME.md"
    if meta_path.exists():
        text = meta_path.read_text(encoding="utf-8")
        meta["raw"] = text
        parsed = _parse_volume_meta(text)
        meta["name"] = meta["name"] or parsed.get("name", "")
        meta["version"] = parsed.get("version") or meta["version"]
        meta["purpose"] = parsed.get("purpose", "")
        if not meta["target_concepts"]:
            meta["target_concepts"] = parsed.get("target_concepts") or []
        if not meta["lessons"]:
            meta["lessons"] = _list_volume_lessons(path)
        meta["volume"] = parsed.get("volume") or meta["volume"]
    elif not meta["lessons"]:
        meta["lessons"] = _list_volume_lessons(path)

    return meta


def _resolve_volume_dir(volume_id: str) -> Optional[Path]:
    if not VOLUMES_DIR.exists():
        return None
    for p in VOLUMES_DIR.iterdir():
        if not p.is_dir():
            continue
        if p.name == volume_id or p.name.startswith(str(volume_id)):
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
    }
    for line in text.splitlines():
        if line.startswith("Volume:"):
            data["volume"] = line.split(":", 1)[1].strip()
        elif line.startswith("Name:"):
            data["name"] = line.split(":", 1)[1].strip()
        elif line.startswith("Version:"):
            data["version"] = line.split(":", 1)[1].strip()

    parts = re.split(r"\n-{5,}\n", text)
    for sec in parts:
        lines = sec.strip().splitlines()
        if not lines:
            continue
        header = lines[0].strip().lower()
        body = "\n".join(lines[1:]).strip()
        if header == "purpose":
            data["purpose"] = body
            concepts = []
            for ln in body.splitlines():
                ln = ln.strip()
                if ln.startswith("-"):
                    concepts.append(ln.lstrip("- ").strip())
            data["target_concepts"] = concepts
    return data


def get_lesson_path(lesson_id: str, volume_id: Optional[str] = None) -> Optional[Path]:
    if volume_id:
        vdir = _resolve_volume_dir(volume_id)
        if vdir:
            for p in (vdir / "lessons").glob(f"{lesson_id}*.md"):
                return p
    if VOLUMES_DIR.exists():
        for vdir in sorted(VOLUMES_DIR.iterdir()):
            lessons = vdir / "lessons"
            if not lessons.exists():
                continue
            for p in lessons.glob(f"{lesson_id}*.md"):
                return p
    legacy = Path(__file__).resolve().parent / "lessons"
    if legacy.exists():
        for p in legacy.glob(f"{lesson_id}*.md"):
            return p
    return None


def load_train_jsonl(volume_id: str = "01") -> List[Dict[str, Any]]:
    vdir = _resolve_volume_dir(volume_id)
    if not vdir:
        return []
    path = vdir / "train.jsonl"
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except Exception:
            pass
    return rows


def load_eval_jsonl(volume_id: str = "01") -> List[Dict[str, Any]]:
    vdir = _resolve_volume_dir(volume_id)
    if not vdir:
        return []
    path = vdir / "eval.jsonl"
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except Exception:
            pass
    return rows
