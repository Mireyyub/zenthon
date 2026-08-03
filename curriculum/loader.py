"""Lesson loader – curriculum/lessons/ altından dərs oxu."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

LESSONS_DIR = Path(__file__).resolve().parent / "lessons"


def list_lessons() -> List[str]:
    if not LESSONS_DIR.exists():
        return []
    ids = []
    for p in sorted(LESSONS_DIR.glob("*.md")):
        # 000001_existence.md → 000001
        m = re.match(r"(\d+)", p.stem)
        if m:
            ids.append(m.group(1))
    return ids


def load_lesson(lesson_id: str) -> Dict[str, Any]:
    """Markdown dərs faylını strukturlaşdırılmış dict-ə çevir."""
    path = _resolve_path(lesson_id)
    if path is None:
        raise FileNotFoundError(f"Lesson not found: {lesson_id}")

    text = path.read_text(encoding="utf-8")
    return parse_lesson_markdown(text, lesson_id=lesson_id, source=str(path))


def _resolve_path(lesson_id: str) -> Optional[Path]:
    if not LESSONS_DIR.exists():
        return None
    # exact or prefix match
    for p in LESSONS_DIR.glob(f"{lesson_id}*.md"):
        return p
    for p in LESSONS_DIR.glob("*.md"):
        if p.stem.startswith(lesson_id):
            return p
    return None


def parse_lesson_markdown(text: str, lesson_id: str = "", source: str = "") -> Dict[str, Any]:
    data: Dict[str, Any] = {
        "id": lesson_id,
        "name": "",
        "version": "1.0",
        "goal": "",
        "concepts": [],
        "rules": [],
        "questions": [],
        "self_tests": [],
        "source": source,
        "raw": text,
    }

    # Header fields
    for line in text.splitlines():
        if line.startswith("Lesson Name:"):
            data["name"] = line.split(":", 1)[1].strip()
        elif line.startswith("Lesson ID:"):
            data["id"] = line.split(":", 1)[1].strip() or lesson_id
        elif line.startswith("Version:"):
            data["version"] = line.split(":", 1)[1].strip()

    # Sections
    sections = re.split(r"\n-{5,}\n", text)
    for sec in sections:
        header = sec.strip().splitlines()[0].strip().upper() if sec.strip() else ""
        body = "\n".join(sec.strip().splitlines()[1:]).strip()

        if header == "GOAL":
            data["goal"] = body
        elif header.startswith("CONCEPT"):
            data["concepts"].append(_parse_concept(header, body))
        elif header == "RULES":
            data["rules"] = [ln.strip() for ln in body.splitlines() if ln.strip()]
        elif header == "QUESTIONS":
            data["questions"] = _parse_questions(body)
        elif header == "SELF TEST":
            data["self_tests"] = _parse_self_tests(body)

    return data


def _parse_concept(header: str, body: str) -> Dict[str, Any]:
    m = re.search(r"CONCEPT\s+(\d+)", header, re.I)
    num = int(m.group(1)) if m else 0
    lines = [ln.strip() for ln in body.splitlines() if ln.strip()]
    statement_lines = []
    examples = []
    props: Dict[str, str] = {}
    mode = "statement"
    for ln in lines:
        low = ln.lower()
        if low.startswith("nümun") or low.startswith("misal") or low.startswith("example"):
            mode = "examples"
            continue
        if ":" in ln and mode != "statement" and len(ln.split(":", 1)[0]) < 20:
            k, v = ln.split(":", 1)
            props[k.strip()] = v.strip()
            continue
        if mode == "examples":
            examples.append(ln)
        else:
            statement_lines.append(ln)
    return {
        "id": num,
        "statement": " ".join(statement_lines).strip(),
        "examples": examples,
        "properties": props,
    }


def _parse_questions(body: str) -> List[Dict[str, str]]:
    qs = []
    q, a = None, None
    for ln in body.splitlines():
        ln = ln.strip()
        if not ln:
            continue
        low = ln.lower()
        if low.startswith("sual") or low.startswith("question"):
            if q and a:
                qs.append({"question": q, "answer": a})
            # next non-empty is question text sometimes on same line
            rest = ln.split(":", 1)[1].strip() if ":" in ln else ""
            q, a = rest or None, None
            continue
        if low.startswith("cavab") or low.startswith("answer"):
            a = ln.split(":", 1)[1].strip() if ":" in ln else ln
            continue
        if q is None:
            q = ln
        elif a is None:
            a = ln
    if q and a:
        qs.append({"question": q, "answer": a})
    return qs


def _parse_self_tests(body: str) -> List[Dict[str, str]]:
    tests = []
    current: Dict[str, str] = {}
    for ln in body.splitlines():
        ln = ln.strip()
        if not ln or ln.startswith("---") or ln.upper().startswith("END"):
            if current.get("input") and current.get("output"):
                tests.append(current)
                current = {}
            continue
        low = ln.lower()
        if low.startswith("input"):
            current["input"] = ln.split(":", 1)[1].strip() if ":" in ln else ""
            if not current["input"]:
                # value on next line style handled by next iteration if empty
                pass
        elif low.startswith("output"):
            current["output"] = ln.split(":", 1)[1].strip() if ":" in ln else ""
        elif "input" in current and not current.get("input"):
            current["input"] = ln
        elif "output" in current and not current.get("output"):
            current["output"] = ln
        elif current.get("input") and not current.get("output"):
            # bare value after Input line
            if "input" in current and current["input"] == "":
                current["input"] = ln
            else:
                current["output"] = ln
        else:
            # alternating bare lines: value after Input header without colon content
            if "pending_input" not in current and low not in ("input", "output"):
                if not current:
                    current = {"input": ln}
                elif "output" not in current:
                    current["output"] = ln
    if current.get("input") and current.get("output"):
        tests.append(current)
    return tests
