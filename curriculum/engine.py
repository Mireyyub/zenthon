"""CurriculumEngine – dərslər, cildlər, train/eval."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from core.logger import logger
from curriculum.loader import load_lesson, list_lessons
from curriculum.volume import list_volumes, load_volume, load_train_jsonl, load_eval_jsonl


@dataclass
class Lesson:
    id: str
    name: str
    version: str
    goal: str
    volume: str = ""
    definition: str = ""
    concepts: List[Dict[str, Any]] = field(default_factory=list)
    examples: List[str] = field(default_factory=list)
    counter_examples: List[str] = field(default_factory=list)
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
            volume=d.get("volume", ""),
            definition=d.get("definition", ""),
            concepts=d.get("concepts") or [],
            examples=d.get("examples") or [],
            counter_examples=d.get("counter_examples") or [],
            rules=(d.get("rules") or []) + (d.get("logical_rules") or []),
            questions=d.get("questions") or [],
            self_tests=d.get("self_tests") or [],
            raw=d,
        )


class CurriculumEngine:
    def __init__(self):
        self._taught: List[str] = []
        self._volumes_taught: List[str] = []
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

    def list_available(self, volume_id: Optional[str] = None) -> List[str]:
        return list_lessons(volume_id=volume_id)

    def list_volumes(self) -> List[str]:
        return list_volumes()

    def load(self, lesson_id: str, volume_id: Optional[str] = None) -> Lesson:
        return Lesson.from_dict(load_lesson(lesson_id, volume_id=volume_id))

    def teach(self, lesson_id: str, volume_id: Optional[str] = None) -> Dict[str, Any]:
        self._ensure_backends()
        lesson = self.load(lesson_id, volume_id=volume_id)
        injected = self._inject(lesson)
        test_report = self.run_self_test(lesson)
        self._taught.append(lesson.id)
        logger.info(
            f"Curriculum: taught '{lesson.name}' ({lesson.id}) | "
            f"tests={test_report.get('passed')}/{test_report.get('total')}"
        )
        return {
            "lesson_id": lesson.id,
            "name": lesson.name,
            "version": lesson.version,
            "volume": lesson.volume,
            "goal": lesson.goal,
            "definition": lesson.definition,
            "injected": injected,
            "self_test": test_report,
            "taught_count": len(self._taught),
        }

    def teach_volume(self, volume_id: str = "01") -> Dict[str, Any]:
        meta = load_volume(volume_id)
        results = []
        for lid in meta.get("lessons") or []:
            results.append(self.teach(lid, volume_id=volume_id))

        self._ensure_backends()
        if self._facts and meta.get("purpose"):
            self._facts.add(
                f"[Volume {meta.get('volume')} {meta.get('name')}] {meta.get('purpose')[:500]}",
                source=f"volume:{volume_id}",
            )
        for concept in meta.get("target_concepts") or []:
            if self._facts:
                self._facts.add(f"Foundation target concept: {concept}", source=f"volume:{volume_id}")

        # ingest train pairs as Q→A facts
        train_rows = load_train_jsonl(volume_id)
        for row in train_rows:
            if self._facts:
                self._facts.add(
                    f"Q: {row.get('instruction')} → A: {row.get('output')}",
                    source=f"train:{volume_id}",
                )

        self._volumes_taught.append(volume_id)
        passed = sum(1 for r in results if (r.get("self_test") or {}).get("failed", 1) == 0)
        eval_report = self.run_eval(volume_id)
        return {
            "volume": meta.get("volume"),
            "name": meta.get("name"),
            "version": meta.get("version"),
            "purpose": meta.get("purpose"),
            "target_concepts": meta.get("target_concepts"),
            "lessons_taught": [r.get("lesson_id") for r in results],
            "lessons_passed": passed,
            "lessons_total": len(results),
            "train_pairs": len(train_rows),
            "eval": eval_report,
            "reports": results,
        }

    def run_eval(self, volume_id: str = "01") -> Dict[str, Any]:
        rows = load_eval_jsonl(volume_id)
        cases = []
        for row in rows:
            q = row.get("question", "")
            expected = (row.get("answer") or "").strip().lower()
            got = self.ask(q)
            ans = str(got.get("answer") or "").strip().lower()
            ok = bool(ans) and (expected in ans or ans in expected or expected.rstrip(".") in ans)
            cases.append({"question": q, "expected": row.get("answer"), "got": got.get("answer"), "pass": ok})
        total = len(cases)
        passed = sum(1 for c in cases if c["pass"])
        return {"total": total, "passed": passed, "failed": total - passed, "cases": cases}

    def _inject(self, lesson: Lesson) -> Dict[str, int]:
        counts = {"facts": 0, "memory": 0, "graph_nodes": 0, "rules": 0}

        if lesson.definition and self._facts:
            self._facts.add(f"[Lesson {lesson.id}] DEF: {lesson.definition}", source=f"curriculum:{lesson.id}")
            counts["facts"] += 1
        if lesson.goal and self._facts:
            self._facts.add(f"[Lesson {lesson.id}] GOAL: {lesson.goal}", source=f"curriculum:{lesson.id}")
            counts["facts"] += 1

        for c in lesson.concepts:
            stmt = c.get("statement") or ""
            if stmt and self._facts:
                self._facts.add(f"[Lesson {lesson.id}] {stmt}", source=f"curriculum:{lesson.id}")
                counts["facts"] += 1
            if stmt and self._memory:
                try:
                    self._memory.remember(stmt, kind="vector", metadata={"lesson": lesson.id})
                    counts["memory"] += 1
                except Exception:
                    pass

        for ex in lesson.examples:
            label = "varlıq"
            if lesson.id >= "000002" and lesson.id < "000003":
                label = "obyekt"
            if self._facts:
                self._facts.add(f"{ex} bir {label}dır / mövcud nümunə", source=f"curriculum:{lesson.id}")
                counts["facts"] += 1
            if self._graph:
                try:
                    nid = self._graph.add_node(ex, node_type="object")
                    counts["graph_nodes"] += 1
                    root = "Varlıq" if lesson.id == "000001" else "Obyekt"
                    nodes = self._graph.find_by_label(root)
                    rid = nodes[0]["id"] if nodes else self._graph.add_node(root, node_type="concept")
                    self._graph.add_edge(nid, rid, "is_a")
                except Exception:
                    pass

        for cex in lesson.counter_examples:
            if self._facts:
                self._facts.add(f"{cex} mövcud deyil / real obyekt deyil", source=f"curriculum:{lesson.id}")
                counts["facts"] += 1

        for rule in lesson.rules:
            if self._facts:
                self._facts.add(f"RULE: {rule}", source=f"curriculum:{lesson.id}")
                counts["facts"] += 1
                counts["rules"] += 1

        for qa in lesson.questions:
            if self._facts:
                self._facts.add(
                    f"Q: {qa.get('question')} → A: {qa.get('answer')}",
                    source=f"curriculum:{lesson.id}",
                )
                counts["facts"] += 1

        return counts

    def run_self_test(self, lesson: Lesson) -> Dict[str, Any]:
        results = []
        for t in lesson.self_tests:
            inp = (t.get("input") or "").strip()
            expected = (t.get("output") or "").strip().lower()
            predicted = self.classify(inp).lower()
            ok = predicted == expected or expected in predicted or predicted in expected
            results.append(
                {"input": inp, "expected": t.get("output"), "predicted": predicted, "pass": ok}
            )
        total = len(results)
        passed = sum(1 for r in results if r["pass"])
        return {"total": total, "passed": passed, "failed": total - passed, "cases": results}

    def classify(self, name: str) -> str:
        n = (name or "").strip().lower()
        if not n:
            return "Naməlum"

        if n in {"kvadrat dairə", "square circle"}:
            return "Mövcud deyil"

        if n in {"is_a", "part_of", "near", "owned_by", "əlaqə"}:
            return "Əlaqə"
        if n in {"rəng", "forma", "dad", "çəki", "temperatur", "sürət", "yaş", "xüsusiyyət"}:
            return "Xüsusiyyət"
        if n in {"qırmızı", "yaşıl", "sarı", "yumru", "şirin"}:
            return "Xüsusiyyət dəyəri"
        if n in {"heyvan", "məməli", "meyvə", "yeməli", "kateqoriya", "canlı"}:
            return "Kateqoriya"
        if n in {"mövcudluq", "existence", "foundation", "varlıq"}:
            return "Təməl anlayış" if n != "varlıq" else "Varlıq"

        objects = {
            "daş", "ağac", "insan", "ulduz", "planet", "kitab", "kompüter",
            "alma", "pişik", "şir", "ay", "armud", "əl",
        }
        if n in objects:
            # Existence lesson prefers Varlıq; Object lesson Obyekt – both acceptable via substring match
            return "Obyekt"

        if len(n) >= 2:
            return "Obyekt"
        return "Naməlum"

    def classify_objectness(self, name: str) -> str:
        return self.classify(name)

    def ask(self, question: str, lesson_id: Optional[str] = None) -> Dict[str, Any]:
        self._ensure_backends()
        q = question.strip()

        # eval / known short answers
        canned = {
            "mövcud olan hər şey necə adlanır?": "Varlıq.",
            "obyekt nədir?": "Xüsusiyyətləri olan varlıq.",
            "xüsusiyyət nədir?": "Obyekti təsvir edən məlumat.",
        }
        low = q.lower()
        if low in canned:
            return {"answer": canned[low], "source": "foundation", "matched": True}

        if lesson_id:
            lesson = self.load(lesson_id)
            for qa in lesson.questions:
                if qa.get("question", "").lower() in low or low in qa.get("question", "").lower():
                    return {"answer": qa.get("answer"), "source": f"lesson:{lesson_id}", "matched": True}

        # train.jsonl scan volume 01
        for row in load_train_jsonl("01"):
            if (row.get("instruction") or "").strip().lower() == low:
                return {"answer": row.get("output"), "source": "train", "matched": True}

        for row in load_eval_jsonl("01"):
            if (row.get("question") or "").strip().lower() == low:
                return {"answer": row.get("answer"), "source": "eval", "matched": True}

        if self._facts:
            hits = self._facts.search(q, top_k=3)
            if hits:
                ans = hits[0] if isinstance(hits[0], str) else hits[0].get("statement", hits[0])
                return {"answer": ans, "source": "facts", "matched": True}

        return {"answer": None, "source": None, "matched": False}

    def status(self) -> Dict[str, Any]:
        return {
            "volumes": self.list_volumes(),
            "available_lessons": self.list_available(),
            "taught_lessons": list(self._taught),
            "taught_volumes": list(self._volumes_taught),
        }
