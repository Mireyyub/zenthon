"""Lesson loader – volumes + legacy lessons + Definition/Rules/Exercises."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from curriculum.volume import get_lesson_path, list_volumes, load_volume

LESSONS_DIR = Path(__file__).resolve().parent / "lessons"


def list_lessons(volume_id: Optional[str] = None) -> List[str]:
    if volume_id:
        try:
            return load_volume(volume_id).get("lessons") or []
        except FileNotFoundError:
            return []
    ids: List[str] = []
    for vid in list_volumes():
        try:
            ids.extend(load_volume(vid).get("lessons") or [])
        except Exception:
            pass
    if LESSONS_DIR.exists():
        for p in sorted(LESSONS_DIR.glob("*.md")):
            m = re.match(r"(\d+)", p.stem)
            if m and m.group(1) not in ids:
                ids.append(m.group(1))
    return sorted(set(ids))


def load_lesson(lesson_id: str, volume_id: Optional[str] = None) -> Dict[str, Any]:
    path = get_lesson_path(lesson_id, volume_id=volume_id)
    if path is None and LESSONS_DIR.exists():
        for p in LESSONS_DIR.glob(f"{lesson_id}*.md"):
            path = p
            break
    if path is None:
        raise FileNotFoundError(f"Lesson not found: {lesson_id}")
    text = path.read_text(encoding="utf-8")
    return parse_lesson_markdown(text, lesson_id=lesson_id, source=str(path))


def parse_lesson_markdown(text: str, lesson_id: str = "", source: str = "") -> Dict[str, Any]:
    data: Dict[str, Any] = {
        "id": lesson_id,
        "name": "",
        "version": "1.0",
        "volume": "",
        "goal": "",
        "definition": "",
        "concepts": [],
        "examples": [],
        "counter_examples": [],
        "logical_rules": [],
        "rules": [],
        "questions": [],
        "self_tests": [],
        "source": source,
        "raw": text,
    }

    for line in text.splitlines():
        if line.startswith("Lesson Name:") or line.startswith("Title"):
            if ":" in line:
                data["name"] = line.split(":", 1)[1].strip()
        elif line.startswith("Lesson ID:"):
            data["id"] = line.split(":", 1)[1].strip() or lesson_id
        elif line.startswith("Version:"):
            data["version"] = line.split(":", 1)[1].strip()
        elif line.startswith("Volume:"):
            data["volume"] = line.split(":", 1)[1].strip()

    # Title on its own line after "Title"
    lines = text.splitlines()
    for i, ln in enumerate(lines):
        if ln.strip() == "Title" and i + 1 < len(lines):
            nxt = lines[i + 1].strip()
            if nxt and not nxt.startswith("#"):
                data["name"] = data["name"] or nxt

    sections = re.split(r"\n-{5,}\n", text)
    for sec in sections:
        if not sec.strip():
            continue
        header = sec.strip().splitlines()[0].strip()
        header_u = header.upper()
        body = "\n".join(sec.strip().splitlines()[1:]).strip()

        if header_u == "GOAL":
            data["goal"] = body
        elif header_u in ("DEFINITION",):
            data["definition"] = body
            data["concepts"].append(
                {"id": 0, "statement": body.replace("\n", " ").strip(), "examples": [], "properties": {}}
            )
        elif header_u in ("EXAMPLES", "NÜMUNƏLƏR"):
            data["examples"] = [ln.strip() for ln in body.splitlines() if ln.strip()]
        elif header_u in ("COUNTER EXAMPLES", "COUNTER_EXAMPLES"):
            data["counter_examples"] = [ln.strip() for ln in body.splitlines() if ln.strip()]
        elif header_u in ("LOGICAL RULES", "LOGICAL_RULES"):
            rules = [ln.strip() for ln in body.splitlines() if ln.strip()]
            data["logical_rules"] = rules
            data["rules"].extend(rules)
        elif header_u == "RULES":
            data["rules"].extend([ln.strip() for ln in body.splitlines() if ln.strip()])
        elif header_u in ("EXERCISES", "QUESTIONS"):
            data["questions"].extend(_parse_questions(body))
        elif header_u.startswith("CONCEPT"):
            data["concepts"].append(_parse_concept(header_u, body))
        elif header_u == "SELF TEST":
            data["self_tests"] = _parse_self_tests(body)

    # Attach examples to first concept if present
    if data["examples"] and data["concepts"]:
        data["concepts"][0]["examples"] = list(
            dict.fromkeys((data["concepts"][0].get("examples") or []) + data["examples"])
        )

    return data


def _parse_concept(header: str, body: str) -> Dict[str, Any]:
    m = re.search(r"CONCEPT\s+(\d+)", header, re.I)
    num = int(m.group(1)) if m else 0
    lines = [ln.strip() for ln in body.splitlines() if ln.strip()]
    statement_lines, examples, props = [], [], {}
    mode = "statement"
    for ln in lines:
        low = ln.lower()
        if low.startswith("nümun") or low.startswith("misal") or low.startswith("example"):
            mode = "examples"
            continue
        if ":" in ln and len(ln.split(":", 1)[0]) < 24:
            k, v = ln.split(":", 1)
            if k.strip().lower() not in {"sual", "cavab", "input", "output"}:
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
    expecting = None
    for ln in body.splitlines():
        ln = ln.strip()
        if not ln or ln.startswith("---") or ln.upper().startswith("END"):
            if current.get("input") and current.get("output"):
                tests.append(current)
                current = {}
            expecting = None
            continue
        low = ln.lower()
        if low.startswith("input"):
            val = ln.split(":", 1)[1].strip() if ":" in ln else ""
            current["input"] = val
            expecting = "input" if not val else None
            continue
        if low.startswith("output"):
            val = ln.split(":", 1)[1].strip() if ":" in ln else ""
            current["output"] = val
            expecting = "output" if not val else None
            continue
        if expecting == "input":
            current["input"] = ln
            expecting = None
        elif expecting == "output":
            current["output"] = ln
            expecting = None
        elif current.get("input") and not current.get("output"):
            current["output"] = ln
    if current.get("input") and current.get("output"):
        tests.append(current)
    return tests
