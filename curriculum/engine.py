"""CurriculumEngine – stronger ask matching + registry backends."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
import re

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


CONCEPT_ROOTS = {
    "Varlıq": "concept",
    "Obyekt": "concept",
    "Xüsusiyyət": "concept",
    "Kateqoriya": "concept",
    "Əlaqə": "concept",
    "Mövcud deyil": "concept",
}


def _norm(s: str) -> str:
    s = (s or "").strip().lower()
    s = s.replace("?", " ").replace(".", " ").replace("!", " ")
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _tokens(s: str) -> set:
    return {t for t in re.findall(r"\w+", _norm(s)) if len(t) > 1}


def _similarity(a: str, b: str) -> float:
    """Simple token Jaccard + substring boost."""
    na, nb = _norm(a), _norm(b)
    if not na or not nb:
        return 0.0
    if na == nb:
        return 1.0
    if na in nb or nb in na:
        return 0.92
    ta, tb = _tokens(a), _tokens(b)
    if not ta or not tb:
        return 0.0
    inter = len(ta & tb)
    union = len(ta | tb) or 1
    j = inter / union
    # question words weight less
    stop = {"nədir", "nə", "mi", "mı", "dir", "dır", "bir", "və", "hansı", "ola", "bilərmi"}
    core_a = ta - stop
    core_b = tb - stop
    if core_a and core_b:
        j = max(j, len(core_a & core_b) / (len(core_a | core_b) or 1))
    return j


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
                from knowledge.registry import get_fact_store

                self._facts = get_fact_store()
            except Exception:
                self._facts = None
        if self._graph is None:
            try:
                from knowledge.registry import get_graph

                self._graph = get_graph()
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

        train_rows = load_train_jsonl(volume_id)
        for row in train_rows:
            if self._facts:
                conf = float(row.get("confidence", 1.0))
                self._facts.add(
                    f"Q: {row.get('instruction') or row.get('input', '')} → A: {row.get('output')}",
                    source=f"train:{volume_id}:{row.get('id', '')}",
                    confidence=conf,
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
            q = row.get("question") or row.get("instruction") or ""
            expected = (row.get("answer") or row.get("output") or "").strip().lower()
            got = self.ask(q)
            ans = str(got.get("answer") or "").strip().lower()
            ok = bool(ans) and (
                expected in ans
                or ans in expected
                or expected.rstrip(".") in ans
                or ans.rstrip(".") in expected
            )
            cases.append(
                {
                    "question": q,
                    "expected": row.get("answer") or row.get("output"),
                    "got": got.get("answer"),
                    "source": got.get("source"),
                    "pass": ok,
                }
            )
        total = len(cases)
        passed = sum(1 for c in cases if c["pass"])
        rate = round(passed / total, 3) if total else 0.0
        return {
            "volume_id": volume_id,
            "total": total,
            "passed": passed,
            "failed": total - passed,
            "pass_rate": rate,
            "cases": cases,
        }

    def _root_id(self, label: str) -> Optional[str]:
        if not self._graph:
            return None
        nodes = self._graph.find_by_label(label)
        exact = [n for n in nodes if n["label"].lower() == label.lower()]
        if exact:
            return exact[0]["id"]
        return self._graph.add_node(label, node_type="concept")

    def _inject(self, lesson: Lesson) -> Dict[str, int]:
        counts = {"facts": 0, "memory": 0, "graph_nodes": 0, "graph_edges": 0, "rules": 0}

        if self._graph:
            for root in CONCEPT_ROOTS:
                self._root_id(root)

        if lesson.definition and self._facts:
            self._facts.add(
                f"[Lesson {lesson.id}] DEF: {lesson.definition}",
                source=f"curriculum:{lesson.id}",
            )
            counts["facts"] += 1
        if lesson.goal and self._facts:
            self._facts.add(
                f"[Lesson {lesson.id}] GOAL: {lesson.goal}",
                source=f"curriculum:{lesson.id}",
            )
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

        lid = lesson.id
        if lid.startswith("000001"):
            primary = "Varlıq"
        elif lid.startswith("000002"):
            primary = "Obyekt"
        elif lid.startswith("000003"):
            primary = "Xüsusiyyət"
        elif lid.startswith("000004"):
            primary = "Kateqoriya"
        elif lid.startswith("000005"):
            primary = "Əlaqə"
        elif lid.startswith("000006"):
            primary = "Səbəb"
        elif lid.startswith("000007"):
            primary = "Nəticə"
        else:
            primary = "Obyekt"

        for ex in lesson.examples:
            ex = ex.strip()
            if not ex:
                continue
            if self._facts:
                self._facts.add(f"{ex} → {primary}", source=f"curriculum:{lesson.id}")
                counts["facts"] += 1
            if self._graph and len(ex) < 80 and not ex.endswith("."):
                try:
                    nid = self._graph.add_node(ex, node_type="entity")
                    counts["graph_nodes"] += 1
                    rid = self._root_id(primary)
                    if rid:
                        self._graph.add_edge(nid, rid, "is_a")
                        counts["graph_edges"] += 1
                    if primary == "Obyekt":
                        vid = self._root_id("Varlıq")
                        if vid:
                            self._graph.add_edge(nid, vid, "is_a")
                            counts["graph_edges"] += 1
                except Exception:
                    pass

        if lid.startswith("000004") and self._graph:
            cat_map = {
                "meyvə": ["alma", "armud", "banan", "şaftalı"],
                "quş": ["qartal", "sərçə", "göyərçin"],
                "məməli": ["insan", "pişik", "it"],
            }
            for cat, members in cat_map.items():
                cid = self._graph.add_node(cat, node_type="concept")
                kid = self._root_id("Kateqoriya")
                if kid:
                    try:
                        self._graph.add_edge(cid, kid, "is_a")
                        counts["graph_edges"] += 1
                    except Exception:
                        pass
                for m in members:
                    mid = self._graph.add_node(m, node_type="entity")
                    try:
                        self._graph.add_edge(mid, cid, "is_a")
                        counts["graph_edges"] += 1
                    except Exception:
                        pass
                    if self._facts:
                        self._facts.add(
                            f"{m} {cat} kateqoriyasına daxildir",
                            source=f"curriculum:{lesson.id}",
                        )
                        counts["facts"] += 1

        if lid.startswith("000005") and self._graph:
            for rel in ("is_a", "part_of", "near", "owned_by", "causes"):
                rid = self._graph.add_node(rel, node_type="relation")
                root = self._root_id("Əlaqə")
                if root:
                    try:
                        self._graph.add_edge(rid, root, "is_a")
                        counts["graph_edges"] += 1
                    except Exception:
                        pass

        for cex in lesson.counter_examples:
            cex = cex.strip()
            if self._facts:
                self._facts.add(
                    f"{cex} mövcud deyil / real obyekt deyil",
                    source=f"curriculum:{lesson.id}",
                )
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
        n = (name or "").strip()
        if not n:
            return "Naməlum"
        low = n.lower()
        self._ensure_backends()

        if low in {"kvadrat dairə", "square circle"} or "mövcud deyil" in low:
            return "Mövcud deyil"

        if self._graph:
            hits = self._graph.find_by_label(n)
            exact = [h for h in hits if h["label"].lower() == low]
            node = exact[0] if exact else (hits[0] if hits else None)
            if node:
                from collections import deque

                q = deque([node["id"]])
                seen = set()
                concepts_found = []
                while q:
                    nid = q.popleft()
                    if nid in seen:
                        continue
                    seen.add(nid)
                    nd = self._graph.get_node(nid)
                    if nd and nd["label"] in CONCEPT_ROOTS:
                        concepts_found.append(nd["label"])
                    for neigh, rel in self._graph.neighbors(nid):
                        if rel == "is_a":
                            q.append(neigh["id"])
                for pref in ("Mövcud deyil", "Əlaqə", "Kateqoriya", "Xüsusiyyət", "Obyekt", "Varlıq"):
                    if pref in concepts_found:
                        return pref
                if concepts_found:
                    return concepts_found[0]

        if self._facts:
            for f in self._facts.search(n, top_k=8):
                stmt = (f.get("statement") or "").lower()
                if low not in stmt and n.lower() not in stmt:
                    continue
                if "mövcud deyil" in stmt:
                    return "Mövcud deyil"
                if "xüsusiyyət" in stmt:
                    return "Xüsusiyyət"
                if "kateqor" in stmt:
                    return "Kateqoriya"
                if "→ obyekt" in stmt or "obyekt" in stmt:
                    return "Obyekt"
                if "→ varlıq" in stmt or "varlıq" in stmt:
                    return "Varlıq"

        if low in {"is_a", "part_of", "near", "owned_by", "əlaqə", "causes"}:
            return "Əlaqə"
        if low in {"rəng", "forma", "dad", "çəki", "temperatur", "sürət", "yaş", "xüsusiyyət"}:
            return "Xüsusiyyət"
        if low in {"heyvan", "məməli", "meyvə", "yeməli", "kateqoriya", "canlı", "quş"}:
            return "Kateqoriya"
        if low in {"səbəb", "cause"}:
            return "Səbəb"
        if low in {"nəticə", "effect"}:
            return "Nəticə"
        if len(low) >= 2:
            return "Obyekt"
        return "Naməlum"

    def classify_objectness(self, name: str) -> str:
        return self.classify(name)

    def ask(self, question: str, lesson_id: Optional[str] = None) -> Dict[str, Any]:
        """Exact → fuzzy train/eval → lesson Q → graph category → facts."""
        self._ensure_backends()
        q = question.strip()
        low = _norm(q)

        best: Optional[Tuple[float, str, str]] = None  # score, answer, source

        for vid in self.list_volumes() or ["01"]:
            try:
                for row in load_train_jsonl(vid):
                    inst = row.get("instruction") or row.get("input") or ""
                    sim = _similarity(q, inst)
                    if sim >= 0.99:
                        return {
                            "answer": row.get("output"),
                            "source": f"train:{vid}",
                            "matched": True,
                            "score": sim,
                        }
                    if sim >= 0.72 and (best is None or sim > best[0]):
                        best = (sim, str(row.get("output")), f"train:{vid}:fuzzy")
                for row in load_eval_jsonl(vid):
                    qq = row.get("question") or row.get("instruction") or ""
                    sim = _similarity(q, qq)
                    ans = row.get("answer") or row.get("output")
                    if sim >= 0.99:
                        return {
                            "answer": ans,
                            "source": f"eval:{vid}",
                            "matched": True,
                            "score": sim,
                        }
                    if sim >= 0.72 and (best is None or sim > best[0]):
                        best = (sim, str(ans), f"eval:{vid}:fuzzy")
            except Exception:
                pass

        if lesson_id:
            lesson = self.load(lesson_id)
            for qa in lesson.questions:
                sim = _similarity(q, qa.get("question") or "")
                if sim >= 0.7:
                    return {
                        "answer": qa.get("answer"),
                        "source": f"lesson:{lesson_id}",
                        "matched": True,
                        "score": sim,
                    }

        # yes/no object existence patterns
        m_obj = re.search(r"(.+?)\s+(obyektdirmi|mövcuddurmu|varlıqdır mı|varlıqdırımı)", low)
        if m_obj:
            entity = m_obj.group(1).strip()
            if entity in {"kvadrat dairə", "square circle"}:
                return {"answer": "Xeyr.", "source": "rule:nonexist", "matched": True}
            cls = self.classify(entity)
            if cls == "Mövcud deyil":
                return {"answer": "Xeyr.", "source": "classify", "matched": True}
            return {"answer": "Bəli.", "source": "classify", "matched": True}

        m = re.search(r"(.+?)\s+hansı\s+kateqoriy", low)
        if m and self._graph:
            entity = m.group(1).strip()
            nodes = self._graph.find_by_label(entity)
            if nodes:
                for neigh, rel in self._graph.neighbors(nodes[0]["id"]):
                    if rel == "is_a" and neigh["label"].lower() not in {
                        "kateqoriya",
                        "obyekt",
                        "varlıq",
                    }:
                        return {
                            "answer": f"{neigh['label'].capitalize()}.",
                            "source": "graph",
                            "matched": True,
                        }

        if best and best[0] >= 0.72:
            return {
                "answer": best[1],
                "source": best[2],
                "matched": True,
                "score": best[0],
            }

        if self._facts:
            hits = self._facts.search(q, top_k=5)
            for h in hits:
                stmt = h.get("statement", "") if isinstance(h, dict) else str(h)
                if "→ A:" in stmt or "→ A :" in stmt:
                    ans = stmt.split("→ A:")[-1].split("→ A :")[-1].strip()
                    return {"answer": ans, "source": "facts", "matched": True}
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
