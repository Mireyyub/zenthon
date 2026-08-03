"""
CurriculumEngine – dərsləri LEON yaddaşına və bilik bazasına yükləyir.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from core.logger import logger
from curriculum.loader import load_lesson, list_lessons


@dataclass
class Lesson:
    id: str
    name: str
    version: str
    goal: str
    concepts: List[Dict[str, Any]] = field(default_factory=list)
    rules: List[str] = field(default_factory=list)
    questions: List[Dict[str, str]] = field(default_factory=list)
    self_tests: List[Dict[str, str]] = field(default_factory=list)
    raw: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Lesson":
        return cls(
            id=d.get("id", ""),
            name=d.get("name", ""),
            version=d.get("version", "1.0"),
            goal=d.get("goal", ""),
            concepts=d.get("concepts") or [],
            rules=d.get("rules") or [],
            questions=d.get("questions") or [],
            self_tests=d.get("self_tests") or [],
            raw=d,
        )


class CurriculumEngine:
    """LEON təlim mühərriki."""

    def __init__(self):
        self._taught: List[str] = []
        self._knowledge = None
        self._memory = None
        self._facts = None
        self._graph = None

    def _ensure_backends(self):
        if self._memory is None:
            try:
                from memory import MemoryManager
                self._memory = MemoryManager()
            except Exception:
                self._memory = None
        if self._knowledge is None:
            try:
                from knowledge import KnowledgeRetrieval
                self._knowledge = KnowledgeRetrieval()
            except Exception:
                self._knowledge = None
        if self._facts is None:
            try:
                from knowledge.facts import FactStore
                self._facts = FactStore()
            except Exception:
                self._facts = None
        if self._graph is None:
            try:
                from knowledge.graph import KnowledgeGraph
                self._graph = KnowledgeGraph()
            except Exception:
                self._graph = None

    def list_available(self) -> List[str]:
        return list_lessons()

    def load(self, lesson_id: str) -> Lesson:
        return Lesson.from_dict(load_lesson(lesson_id))

    def teach(self, lesson_id: str) -> Dict[str, Any]:
        """Dərsi yüklə, bilik/yaddaşa yaz, self-test işlət."""
        self._ensure_backends()
        lesson = self.load(lesson_id)
        injected = self._inject(lesson)
        test_report = self.run_self_test(lesson)
        self._taught.append(lesson.id)

        logger.info(
            f"Curriculum: taught '{lesson.name}' ({lesson.id}) | "
            f"concepts={len(lesson.concepts)} rules={len(lesson.rules)} "
            f"tests_pass={test_report.get('passed')}/{test_report.get('total')}"
        )
        return {
            "lesson_id": lesson.id,
            "name": lesson.name,
            "version": lesson.version,
            "goal": lesson.goal,
            "injected": injected,
            "self_test": test_report,
            "taught_count": len(self._taught),
        }

    def _inject(self, lesson: Lesson) -> Dict[str, int]:
        counts = {"facts": 0, "memory": 0, "graph_nodes": 0, "rules": 0}

        # Goal
        if lesson.goal and self._facts:
            self._facts.add(f"[Lesson {lesson.id}] GOAL: {lesson.goal}", source=f"curriculum:{lesson.id}")
            counts["facts"] += 1

        # Concepts
        for c in lesson.concepts:
            stmt = c.get("statement") or ""
            if stmt and self._facts:
                self._facts.add(
                    f"[Lesson {lesson.id}/C{c.get('id')}] {stmt}",
                    source=f"curriculum:{lesson.id}",
                )
                counts["facts"] += 1
            if stmt and self._memory:
                try:
                    self._memory.remember(stmt, kind="vector", metadata={"lesson": lesson.id})
                    counts["memory"] += 1
                except Exception:
                    pass
            # examples as objects in graph
            for ex in c.get("examples") or []:
                if self._graph:
                    try:
                        nid = self._graph.add_node(ex, node_type="object")
                        counts["graph_nodes"] += 1
                        # link to abstract Object
                        obj_nodes = self._graph.find_by_label("Obyekt")
                        if not obj_nodes:
                            oid = self._graph.add_node("Obyekt", node_type="concept")
                        else:
                            oid = obj_nodes[0]["id"]
                        self._graph.add_edge(nid, oid, "is_a")
                    except Exception:
                        pass
                if self._facts:
                    self._facts.add(f"{ex} bir obyektdir", source=f"curriculum:{lesson.id}")
                    counts["facts"] += 1

            for k, v in (c.get("properties") or {}).items():
                if self._facts:
                    self._facts.add(f"xüsusiyyət {k} = {v}", source=f"curriculum:{lesson.id}")
                    counts["facts"] += 1

        # Rules
        for rule in lesson.rules:
            if self._facts:
                self._facts.add(f"RULE: {rule}", source=f"curriculum:{lesson.id}")
                counts["facts"] += 1
                counts["rules"] += 1
            if self._memory:
                try:
                    self._memory.remember(f"RULE: {rule}", kind="vector", metadata={"lesson": lesson.id, "type": "rule"})
                    counts["memory"] += 1
                except Exception:
                    pass

        # Q&A as facts
        for qa in lesson.questions:
            if self._facts:
                self._facts.add(
                    f"Q: {qa.get('question')} → A: {qa.get('answer')}",
                    source=f"curriculum:{lesson.id}",
                )
                counts["facts"] += 1

        # Knowledge retrieval ingest if available
        if self._knowledge:
            try:
                entities = []
                for c in lesson.concepts:
                    entities.extend(c.get("examples") or [])
                self._knowledge.add_knowledge(
                    f"Lesson {lesson.id} {lesson.name}: {lesson.goal}",
                    entities=list(dict.fromkeys(entities))[:20],
                )
            except Exception:
                pass

        return counts

    def run_self_test(self, lesson: Lesson) -> Dict[str, Any]:
        """SELF TEST blokunu yoxla."""
        results = []
        for t in lesson.self_tests:
            inp = (t.get("input") or "").strip()
            expected = (t.get("output") or "").strip().lower()
            # Minimal classifier for Existence lesson
            predicted = self.classify_objectness(inp).lower()
            ok = predicted == expected or expected in predicted or predicted in expected
            results.append(
                {
                    "input": inp,
                    "expected": t.get("output"),
                    "predicted": predicted,
                    "pass": ok,
                }
            )
        total = len(results)
        passed = sum(1 for r in results if r["pass"])
        return {"total": total, "passed": passed, "failed": total - passed, "cases": results}

    def classify_objectness(self, name: str) -> str:
        """
        Existence dərsi üçün sadə təsnifat.
        Məlum nümunələr + ümumi qayda: müşahidə oluna bilən → Obyekt.
        """
        n = (name or "").strip().lower()
        if not n:
            return "Naməlum"
        known_objects = {
            "daş",
            "ağac",
            "insan",
            "ulduz",
            "planet",
            "kitab",
            "kompüter",
            "alma",
            "pişik",
            "şir",
            "qırmızı alma",
        }
        if n in known_objects:
            return "Obyekt"
        # generic: non-empty concrete noun-like tokens treated as object candidates
        if len(n) >= 2 and n not in {"yox", "heç", "yoxdur", "nothing", "none"}:
            return "Obyekt"
        return "Naməlum"

    def ask(self, question: str, lesson_id: Optional[str] = None) -> Dict[str, Any]:
        """Dərs suallarına və ya bilik bazasına əsasən cavab."""
        self._ensure_backends()
        q = question.strip()

        if lesson_id:
            lesson = self.load(lesson_id)
            for qa in lesson.questions:
                if qa.get("question", "").lower() in q.lower() or q.lower() in qa.get("question", "").lower():
                    return {"answer": qa.get("answer"), "source": f"lesson:{lesson_id}", "matched": True}

            # objectness questions
            low = q.lower()
            if "obyekt" in low:
                # extract candidate word
                for token in re_tokens(q):
                    if token not in {"obyekt", "obyektdirmi", "mi", "mı", "dir", "dərmi"}:
                        if self.classify_objectness(token) == "Obyekt":
                            return {"answer": "Bəli", "source": "curriculum:objectness", "matched": True}
                return {"answer": "Bəli" if "obyekt" in low else "Naməlum", "source": "heuristic", "matched": False}

        if self._facts:
            hits = self._facts.search(q, top_k=3)
            if hits:
                return {"answer": hits[0] if isinstance(hits[0], str) else hits[0].get("statement", hits[0]), "source": "facts", "matched": True}

        return {"answer": None, "source": None, "matched": False}

    def status(self) -> Dict[str, Any]:
        return {
            "available_lessons": self.list_available(),
            "taught": list(self._taught),
        }


def re_tokens(text: str) -> List[str]:
    import re

    return re.findall(r"\w+", text.lower())
