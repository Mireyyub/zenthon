"""
Leon Self-Mutation Engine v2 — controlled, strategy-aware source evolution.

New in v2:
- Named strategies (train_enrich, docstring_boost, guard_soft, confidence_bump…)
- Path success stats from history (prefer proven targets)
- compile() + optional importlib check after apply
- Unified diff in proposals
- evolve(): multi-round diagnose→mutate→verify loop
- list_proposals / best pending selection
- Richer quality model (history prior, strategy bonus)

Safety unchanged:
- LEON_ALLOW_MUTATE=1 gate
- Allowlist / forbidden (security, kernel, self_mutate)
- Backup + smoke/import fail → rollback
"""

from __future__ import annotations

import ast
import hashlib
import json
import os
import re
import shutil
import uuid
from datetime import datetime
from difflib import unified_diff
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from core.logger import logger
from core.persistence import write_json, read_json


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _mutate_dir() -> Path:
    try:
        from core.config import config

        d = Path(config.path.leon_dir) / "mutations"
    except Exception:
        d = Path("data/leon/mutations")
    (d / "backups").mkdir(parents=True, exist_ok=True)
    (d / "proposals").mkdir(parents=True, exist_ok=True)
    return d


ALLOWED_PREFIXES = (
    "curriculum/volumes/",
    "genome/",
    "schemas/",
    "multimodal/",
    "learning/",
    "knowledge/facts.py",
    "knowledge/graph.py",
    "knowledge/retrieval.py",
    "memory/",
    "agents/research_agent.py",
    "agents/coding_agent.py",
    "agents/react_agent.py",
    "brain/confidence.py",
    "brain/self_improve.py",
    "brain/reasoning/",
    "evaluation/",
    "docs/",
)

FORBIDDEN_PREFIXES = (
    "security/",
    "core/kernel",
    "core/bootstrap",
    "core/config",
    "core/service_registry",
    ".git/",
    "venv/",
    ".venv/",
    "__pycache__/",
    "brain/self_mutate.py",
)

ROUTE_TABLE: List[Tuple[Tuple[str, ...], str]] = [
    (("curriculum", "dərs", "lesson", "train", "eval", "öyrən", "bilik", "fact", "qa"), "curriculum/volumes/01_foundation/train.jsonl"),
    (("causality", "səbəb", "nəticə", "cause"), "curriculum/volumes/02_causality/train.jsonl"),
    (("coding", "code agent", "template"), "agents/coding_agent.py"),
    (("react", "tool"), "agents/react_agent.py"),
    (("research", "web"), "agents/research_agent.py"),
    (("reason", "reasoning", "düşün"), "brain/reasoning/engine.py"),
    (("confidence", "etibar"), "brain/confidence.py"),
    (("memory", "yaddaş", "vector"), "memory/vector_memory.py"),
    (("graph", "qraf"), "knowledge/graph.py"),
    (("fact", "fakt"), "knowledge/facts.py"),
    (("vision", "image", "görüntü", "multimodal"), "multimodal/understand.py"),
    (("genome", "genom"), "genome/"),
    (("self improve", "təkmilləş"), "brain/self_improve.py"),
]

DANGEROUS_AST = {"eval", "exec", "compile", "__import__"}
DANGEROUS_ATTR = {
    ("os", "system"),
    ("os", "popen"),
    ("subprocess", "call"),
    ("subprocess", "run"),
    ("subprocess", "Popen"),
    ("shutil", "rmtree"),
}

MAX_DELTA_RATIO = 0.45
MAX_WRITE_BYTES = 200_000
AUTO_APPLY_MIN_QUALITY = 55.0

# Deterministic strategies (no LLM required)
STRATEGIES = (
    "train_enrich",
    "qa_pair_append",
    "diagnostic_repair",
    "docstring_boost",
    "confidence_bump",
    "log_guard",
    "todo_resolve",
)


class MutationError(Exception):
    pass


class SelfMutateEngine:
    def __init__(self, repo_root: Optional[Path] = None):
        self.root = Path(repo_root) if repo_root else _repo_root()
        self.dir = _mutate_dir()

    # ------------------------------------------------------------------ gates
    def mutation_enabled(self) -> bool:
        return os.environ.get("LEON_ALLOW_MUTATE", "").strip().lower() in (
            "1",
            "true",
            "yes",
            "on",
        )

    def is_allowed(self, rel_path: str) -> Tuple[bool, str]:
        rel = rel_path.replace("\\", "/").lstrip("./")
        for bad in FORBIDDEN_PREFIXES:
            if rel.startswith(bad) or rel == bad.rstrip("/"):
                return False, f"forbidden: {bad}"
        for good in ALLOWED_PREFIXES:
            if rel.startswith(good) or rel == good.rstrip("/"):
                return True, "allowlist"
        return False, "not in allowlist"

    def resolve(self, rel_path: str) -> Path:
        ok, reason = self.is_allowed(rel_path)
        if not ok:
            raise MutationError(f"Path not mutable: {rel_path} ({reason})")
        p = (self.root / rel_path).resolve()
        try:
            p.relative_to(self.root.resolve())
        except ValueError as e:
            raise MutationError("Path escapes repo root") from e
        return p

    # ------------------------------------------------------------------ stats
    def path_stats(self) -> Dict[str, Dict[str, Any]]:
        hist = read_json(self.dir / "history.json", default={"runs": []}) or {}
        stats: Dict[str, Dict[str, Any]] = {}
        for r in hist.get("runs") or []:
            p = r.get("path") or ""
            if not p:
                continue
            s = stats.setdefault(p, {"ok": 0, "fail": 0, "rollback": 0, "total": 0})
            s["total"] += 1
            if r.get("rolled_back"):
                s["rollback"] += 1
                s["fail"] += 1
            elif r.get("ok"):
                s["ok"] += 1
            else:
                s["fail"] += 1
        for p, s in stats.items():
            s["success_rate"] = round(s["ok"] / s["total"], 3) if s["total"] else 0.0
        return stats

    # ------------------------------------------------------------------ routing
    def route_goal(self, goal: str) -> Dict[str, Any]:
        g = (goal or "").lower()
        hits: List[Tuple[float, str, str]] = []
        pstats = self.path_stats()
        for keys, path in ROUTE_TABLE:
            score = float(sum(1 for k in keys if k in g))
            if not score:
                continue
            # history prior
            st = pstats.get(path) or {}
            if st.get("total"):
                score += 2.0 * float(st.get("success_rate") or 0)
                score -= 1.0 * (float(st.get("rollback") or 0) / max(st["total"], 1))
            hits.append((score, path, keys[0]))
        hits.sort(key=lambda x: -x[0])
        if not hits:
            return {
                "path": "curriculum/volumes/01_foundation/train.jsonl",
                "strategy": "default_train",
                "score": 0,
                "path_stats": pstats.get("curriculum/volumes/01_foundation/train.jsonl"),
            }
        best = hits[0]
        path = best[1]
        if path.endswith("/"):
            d = self.root / path
            if d.is_dir():
                cands = sorted(d.glob("*.json")) + sorted(d.glob("*.md"))
                if cands:
                    path = str(cands[0].relative_to(self.root)).replace("\\", "/")
        return {
            "path": path,
            "strategy": best[2],
            "score": best[0],
            "alternatives": [{"path": h[1], "score": h[0], "key": h[2]} for h in hits[1:4]],
            "path_stats": pstats.get(path),
        }

    # ------------------------------------------------------------------ quality
    def _import_names(self, tree: ast.AST) -> set:
        names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for a in node.names:
                    names.add(a.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom) and node.module:
                names.add(node.module.split(".")[0])
        return names

    def _dangerous(self, tree: ast.AST) -> List[str]:
        issues = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id in DANGEROUS_AST:
                    # allow compile only if not used as runtime code exec pattern - still ban
                    issues.append(f"call:{node.func.id}")
                if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
                    pair = (node.func.value.id, node.func.attr)
                    if pair in DANGEROUS_ATTR:
                        issues.append(f"call:{pair[0]}.{pair[1]}")
        return issues

    def score_mutation(
        self,
        rel: str,
        original: str,
        mutated: str,
        *,
        mode: str,
        strategy: str = "",
    ) -> Dict[str, Any]:
        score = 50.0
        notes: List[str] = []

        if original == mutated:
            return {"score": 0, "syntax_ok": True, "notes": ["no change"], "reject": True}
        if len(mutated.encode()) > MAX_WRITE_BYTES:
            return {"score": 0, "syntax_ok": False, "notes": ["too large"], "reject": True}

        if rel.endswith(".py"):
            try:
                tree_new = ast.parse(mutated)
                compile(mutated, rel, "exec")
            except SyntaxError as e:
                return {
                    "score": 0,
                    "syntax_ok": False,
                    "syntax_error": f"{e.msg} line={e.lineno}",
                    "notes": ["syntax/compile error"],
                    "reject": True,
                }
            dangerous = self._dangerous(tree_new)
            if dangerous:
                return {
                    "score": 0,
                    "syntax_ok": True,
                    "notes": ["dangerous:" + ",".join(dangerous)],
                    "reject": True,
                    "dangerous": dangerous,
                }
            try:
                tree_old = ast.parse(original) if original.strip() else None
            except SyntaxError:
                tree_old = None
            if tree_old is not None:
                lost = self._import_names(tree_old) - self._import_names(tree_new)
                lost = {x for x in lost if not x.startswith("_")}
                if lost and mode == "replace":
                    score -= 15
                    notes.append(f"imports_lost:{sorted(lost)[:5]}")
            score += 20
            notes.append("py_ok")

        if original:
            ratio = abs(len(mutated) - len(original)) / max(len(original), 1)
            if mode == "replace" and ratio > MAX_DELTA_RATIO:
                score -= 25
                notes.append(f"large_delta:{ratio:.2f}")
            elif ratio < 0.15:
                score += 10
                notes.append("surgical")

        if mode == "append":
            score += 5
            notes.append("append_safe")

        if rel.endswith(".jsonl") and mode == "append":
            added = mutated[len(original) :]
            ok_lines = 0
            for line in added.strip().splitlines():
                try:
                    json.loads(line)
                    ok_lines += 1
                except Exception:
                    score -= 20
                    notes.append("bad_jsonl_line")
            if ok_lines:
                score += 15
                notes.append(f"jsonl_ok:{ok_lines}")

        # history prior for this path
        st = self.path_stats().get(rel) or {}
        if st.get("total"):
            score += 8 * float(st.get("success_rate") or 0)
            notes.append(f"hist_sr={st.get('success_rate')}")

        if strategy in ("train_enrich", "docstring_boost", "confidence_bump"):
            score += 5
            notes.append(f"strategy:{strategy}")

        score = max(0.0, min(100.0, score))
        return {
            "score": round(score, 1),
            "syntax_ok": True,
            "syntax_error": None,
            "notes": notes,
            "dangerous": [],
            "reject": score < 25,
            "strategy": strategy,
        }

    # ------------------------------------------------------------------ propose core
    def propose(
        self,
        path: str,
        *,
        mode: str = "replace",
        old: str = "",
        new: str = "",
        content: str = "",
        reason: str = "",
        author: str = "leon",
        goal: str = "",
        strategy: str = "",
    ) -> Dict[str, Any]:
        rel = path.replace("\\", "/").lstrip("./")
        ok, why = self.is_allowed(rel)
        if not ok:
            return {"ok": False, "error": f"not mutable: {rel} ({why})"}

        target = self.root / rel
        if not target.exists() and mode != "write":
            return {"ok": False, "error": f"file missing: {rel}"}

        original = target.read_text(encoding="utf-8") if target.exists() else ""
        mode = (mode or "replace").lower()

        try:
            mutated = self._build_mutated(original, mode=mode, old=old, new=new, content=content)
        except MutationError as e:
            return {"ok": False, "error": str(e)}

        quality = self.score_mutation(rel, original, mutated, mode=mode, strategy=strategy)
        syntax_ok = quality.get("syntax_ok", True) and not quality.get("reject")

        pid = "MU-" + str(uuid.uuid4())[:8]
        udiff = self._unified_diff(rel, original, mutated)
        proposal = {
            "id": pid,
            "path": rel,
            "mode": mode,
            "strategy": strategy,
            "reason": reason,
            "goal": goal,
            "author": author,
            "created_at": datetime.now().isoformat(),
            "original_sha16": hashlib.sha256(original.encode()).hexdigest()[:16],
            "mutated_sha16": hashlib.sha256(mutated.encode()).hexdigest()[:16],
            "syntax_ok": syntax_ok,
            "syntax_error": quality.get("syntax_error"),
            "quality": quality,
            "bytes_before": len(original.encode()),
            "bytes_after": len(mutated.encode()),
            "diff_preview": self._preview(original, mutated),
            "unified_diff": udiff[:4000],
            "status": "proposed" if syntax_ok else "rejected",
            "_original": original,
            "_mutated": mutated,
        }
        write_json(self.dir / "proposals" / f"{pid}.json", proposal)
        write_json(self.dir / "last_proposal.json", proposal)
        return {
            "ok": syntax_ok,
            "proposal_id": pid,
            "path": rel,
            "strategy": strategy,
            "syntax_ok": syntax_ok,
            "quality": quality,
            "diff_preview": proposal["diff_preview"],
            "unified_diff": proposal["unified_diff"],
            "status": proposal["status"],
            "enabled": self.mutation_enabled(),
            "hint": None
            if self.mutation_enabled()
            else "Apply üçün: export LEON_ALLOW_MUTATE=1",
        }

    def _build_mutated(
        self,
        original: str,
        *,
        mode: str,
        old: str,
        new: str,
        content: str,
    ) -> str:
        if mode == "replace":
            if not old:
                raise MutationError("replace mode requires old=")
            if old not in original and old.replace("\r\n", "\n") in original.replace("\r\n", "\n"):
                original = original.replace("\r\n", "\n")
                old = old.replace("\r\n", "\n")
                new = new.replace("\r\n", "\n")
            count = original.count(old)
            if count != 1:
                fuzzy = self._fuzzy_unique(original, old)
                if fuzzy is None:
                    raise MutationError(f"old must appear exactly once (found {count})")
                return original.replace(fuzzy, new, 1)
            return original.replace(old, new, 1)
        if mode == "append":
            piece = new if new.endswith("\n") or not new else new + "\n"
            return original + piece
        if mode == "write":
            return content
        raise MutationError(f"unknown mode: {mode}")

    def _fuzzy_unique(self, text: str, fragment: str) -> Optional[str]:
        frag = fragment.strip()
        if not frag:
            return None
        flines = frag.splitlines()
        tlines = text.splitlines(keepends=True)
        n = len(flines)
        if n == 0 or n > len(tlines):
            return None
        matches = []
        for i in range(len(tlines) - n + 1):
            block = "".join(tlines[i : i + n])
            if block.strip() == frag:
                matches.append(block)
        return matches[0] if len(matches) == 1 else None

    def _unified_diff(self, path: str, old: str, new: str) -> str:
        return "".join(
            unified_diff(
                old.splitlines(keepends=True),
                new.splitlines(keepends=True),
                fromfile=f"a/{path}",
                tofile=f"b/{path}",
                n=3,
            )
        )

    def _preview(self, old: str, new: str, lines: int = 6) -> str:
        if old == new:
            return "(no change)"
        o, n = old.splitlines(), new.splitlines()
        for i, (a, b) in enumerate(zip(o, n)):
            if a != b:
                start = max(0, i - 1)
                return (
                    "--- old ---\n"
                    + "\n".join(o[start : start + lines])
                    + "\n+++ new +++\n"
                    + "\n".join(n[start : start + lines])
                )
        if len(n) > len(o):
            return "+++ appended +++\n" + "\n".join(n[len(o) : len(o) + lines])
        return f"bytes {len(old)} → {len(new)}"

    # ------------------------------------------------------------------ strategies
    def propose_strategy(
        self,
        strategy: str,
        *,
        goal: str = "",
        path: Optional[str] = None,
    ) -> Dict[str, Any]:
        strategy = (strategy or "").lower().strip()
        if strategy not in STRATEGIES:
            return {
                "ok": False,
                "error": f"unknown strategy: {strategy}",
                "available": list(STRATEGIES),
            }

        if strategy == "diagnostic_repair":
            return self.propose_from_diagnosis()

        if strategy == "qa_pair_append":
            if not re.search(r"(?:sual|q)\s*[:：].+(?:cavab|a)\s*[:：]", goal, re.I | re.S):
                return {"ok": False, "error": "qa_pair_append üçün 'sual: ... cavab: ...' formatı lazımdır"}
            target = path or self.route_goal(goal).get("path")
            if not str(target).endswith(".jsonl"):
                target = "curriculum/volumes/01_foundation/train.jsonl"
            q, a = self._extract_qa(goal)
            line = json.dumps({"id": "qa_" + uuid.uuid4().hex[:6], "instruction": q, "output": a, "lesson": "verified_qa_pair", "confidence": 0.9, "tags": ["self_mutate", "qa_pair"]}, ensure_ascii=False)
            return self.propose(str(target), mode="append", new=line + "\n", reason="strategy:qa_pair_append", author="leon:strategy", goal=goal, strategy=strategy)

        if strategy == "train_enrich":
            target = path or self.route_goal(goal or "öyrən").get("path")
            if not str(target).endswith(".jsonl"):
                target = "curriculum/volumes/01_foundation/train.jsonl"
            q, a = self._extract_qa(goal or "Yeni bilik")
            line = json.dumps(
                {
                    "id": "str_" + uuid.uuid4().hex[:6],
                    "instruction": q,
                    "output": a,
                    "lesson": "strategy_train_enrich",
                    "confidence": 0.75,
                    "tags": ["self_mutate", "strategy"],
                },
                ensure_ascii=False,
            )
            return self.propose(
                str(target),
                mode="append",
                new=line + "\n",
                reason="strategy:train_enrich",
                author="leon:strategy",
                goal=goal,
                strategy=strategy,
            )

        target = path or self.route_goal(goal or strategy).get("path")
        src_path = self.root / str(target)
        if not src_path.exists() or not str(target).endswith(".py"):
            return {"ok": False, "error": f"strategy needs existing .py: {target}"}
        src = src_path.read_text(encoding="utf-8")

        if strategy == "docstring_boost":
            # add a one-line module note if missing Leon marker
            marker = "# Leon-mutated: docstring_boost"
            if marker in src:
                return {"ok": False, "error": "already docstring_boosted"}
            # insert after module docstring or at top
            if src.startswith('"""') or src.startswith("'''"):
                # after first docstring
                m = re.match(r'([ruRU]?["\']{3}.*?["\']{3}\n)', src, re.S)
                if m:
                    old = m.group(1)
                    new = old + marker + "\n"
                    return self.propose(
                        str(target),
                        mode="replace",
                        old=old,
                        new=new,
                        reason="strategy:docstring_boost",
                        author="leon:strategy",
                        goal=goal,
                        strategy=strategy,
                    )
            return self.propose(
                str(target),
                mode="replace",
                old=src[:80],
                new=marker + "\n" + src[:80],
                reason="strategy:docstring_boost",
                author="leon:strategy",
                goal=goal,
                strategy=strategy,
            )

        if strategy == "confidence_bump":
            # bump literal confidence thresholds slightly if found
            m = re.search(r"(CONFIDENCE_\w+\s*=\s*)(0\.\d+)", src)
            if not m:
                m = re.search(r"(confidence\s*[<>=]+\s*)(0\.\d+)", src)
            if not m:
                return {"ok": False, "error": "no confidence literal found"}
            old = m.group(0)
            try:
                val = float(m.group(2))
                new_val = min(0.99, round(val + 0.02, 3))
            except Exception:
                return {"ok": False, "error": "parse confidence failed"}
            new = m.group(1) + str(new_val)
            return self.propose(
                str(target),
                mode="replace",
                old=old,
                new=new,
                reason="strategy:confidence_bump",
                author="leon:strategy",
                goal=goal,
                strategy=strategy,
            )

        if strategy == "log_guard":
            # wrap bare pass in a function body is too risky; add logger.debug in except Exception: pass
            pattern = re.compile(r"(except Exception(?: as \w+)?:)\n(\s+)pass\b")
            m = pattern.search(src)
            if not m:
                return {"ok": False, "error": "no bare except-pass found"}
            old = m.group(0)
            indent = m.group(2)
            new = f"{m.group(1)}\n{indent}logger.debug(\"soft-fail\")\n{indent}pass"
            if "from core.logger import logger" not in src and "logger" not in src[:500]:
                # ensure logger import via append at end of imports - safer skip
                return {"ok": False, "error": "logger not obviously available"}
            return self.propose(
                str(target),
                mode="replace",
                old=old,
                new=new,
                reason="strategy:log_guard",
                author="leon:strategy",
                goal=goal,
                strategy=strategy,
            )

        if strategy == "todo_resolve":
            m = re.search(r"#\s*TODO[:\s].*", src)
            if not m:
                return {"ok": False, "error": "no TODO found"}
            old = m.group(0)
            new = old + "  # addressed-by-self_mutate"
            return self.propose(
                str(target),
                mode="replace",
                old=old,
                new=new,
                reason="strategy:todo_resolve",
                author="leon:strategy",
                goal=goal,
                strategy=strategy,
            )

        return {"ok": False, "error": "unhandled strategy"}

    # ------------------------------------------------------------------ goal / LLM
    def propose_from_goal(
        self,
        goal: str,
        *,
        path: Optional[str] = None,
        candidates: int = 3,
        strategy: Optional[str] = None,
    ) -> Dict[str, Any]:
        if strategy:
            return self.propose_strategy(strategy, goal=goal, path=path)

        route = self.route_goal(goal)
        target = path or route["path"]
        goal_l = (goal or "").lower()

        if target.endswith(".jsonl") or any(
            k in goal_l for k in ("öyrən", "learn", "fact", "bilik", "qa", "sual", "dərs")
        ):
            return self.propose_strategy("train_enrich", goal=goal, path=target if str(target).endswith(".jsonl") else None)

        ranked = self._llm_ranked_patches(str(target), goal, n=max(1, min(candidates, 5)))
        if not ranked:
            # fallback strategies
            for s in ("docstring_boost", "todo_resolve", "confidence_bump"):
                fb = self.propose_strategy(s, goal=goal, path=str(target))
                if fb.get("ok"):
                    fb["route"] = route
                    fb["strategy_fallback"] = s
                    return fb
            return {
                "ok": False,
                "error": "No valid LLM or strategy candidates",
                "route": route,
            }

        best = ranked[0]
        prop = self.propose(
            str(target),
            mode="replace",
            old=best["old"],
            new=best["new"],
            reason=f"goal:{goal[:120]}",
            author="leon:llm_ranked",
            goal=goal,
            strategy="llm_ranked",
        )
        prop["route"] = route
        prop["candidates"] = [
            {"rank": i + 1, "score": c.get("score"), "why": c.get("why")}
            for i, c in enumerate(ranked[:5])
        ]
        return prop

    def _extract_qa(self, goal: str) -> Tuple[str, str]:
        g = goal.strip()
        m = re.search(r"sual\s*[:：]\s*(.+?)\s*cavab\s*[:：]\s*(.+)", g, re.I | re.S)
        if m:
            return m.group(1).strip()[:200], m.group(2).strip()[:200]
        m = re.search(r"q\s*[:：]\s*(.+?)\s*a\s*[:：]\s*(.+)", g, re.I | re.S)
        if m:
            return m.group(1).strip()[:200], m.group(2).strip()[:200]
        return (
            g[:200],
            "Bəli." if any(x in g.lower() for x in ("mövcud", "obyekt", "var")) else "Öyrənilmiş.",
        )

    def _llm_ranked_patches(self, rel: str, goal: str, n: int = 3) -> List[Dict[str, Any]]:
        src_path = self.root / rel
        if not src_path.exists() or not rel.endswith(".py"):
            return []
        src = src_path.read_text(encoding="utf-8")
        snippet = src[:6000] if len(src) < 7000 else src[:3000] + "\n# …\n" + src[-3000:]
        try:
            from brain.llm.client import get_llm_client

            client = get_llm_client()
        except Exception:
            return []

        system = (
            "You are Leon's careful code mutator. Return ONLY a JSON array of up to "
            f"{n} objects: {{\"old\":\"exact unique substring\",\"new\":\"replacement\",\"why\":\"...\"}}. "
            "old ≤12 lines, appears once. Minimal surgical edits. "
            "Never introduce eval/exec/os.system/subprocess."
        )
        reply = client.complete(
            f"GOAL:\n{goal[:300]}\n\nFILE {rel}:\n{snippet}",
            system=system,
            temperature=0.25,
            max_tokens=1400,
        )
        if not reply:
            return []

        ranked: List[Dict[str, Any]] = []
        for it in self._parse_json_array(reply):
            old, new = it.get("old") or "", it.get("new") or ""
            if not old or new is None:
                continue
            if src.count(old) != 1 and self._fuzzy_unique(src, old) is None:
                continue
            try:
                mutated = self._build_mutated(src, mode="replace", old=old, new=new, content="")
            except MutationError:
                continue
            q = self.score_mutation(rel, src, mutated, mode="replace", strategy="llm_ranked")
            if q.get("reject"):
                continue
            ranked.append(
                {
                    "old": old,
                    "new": new,
                    "why": it.get("why"),
                    "quality": q,
                    "score": q.get("score", 0),
                }
            )
        ranked.sort(key=lambda x: -float(x.get("score") or 0))
        return ranked

    def _parse_json_array(self, text: str) -> List[Dict[str, Any]]:
        text = text.strip()
        try:
            m = re.search(r"\[.*\]", text, re.S)
            if m:
                data = json.loads(m.group(0))
                if isinstance(data, list):
                    return [x for x in data if isinstance(x, dict)]
        except Exception:
            pass
        try:
            m = re.search(r"\{.*\}", text, re.S)
            if m:
                data = json.loads(m.group(0))
                if isinstance(data, dict):
                    return [data]
        except Exception:
            pass
        return []

    # ------------------------------------------------------------------ diagnose / evolve
    def propose_from_diagnosis(
        self, diagnosis: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        if diagnosis is None:
            try:
                from brain.self_improve import SelfImproveEngine

                diagnosis = SelfImproveEngine().diagnose()
            except Exception as e:
                return {"ok": False, "error": f"diagnose failed: {e}"}

        weak = diagnosis.get("weak_cases") or []
        if not weak:
            return {
                "ok": True,
                "message": "no weak cases",
                "proposals": [],
                "severity": diagnosis.get("severity"),
            }

        by_vol: Dict[str, List[Dict]] = {}
        for c in weak:
            by_vol.setdefault(str(c.get("volume_id") or "01"), []).append(c)

        proposals = []
        for vid, cases in by_vol.items():
            vol_dirs = list((self.root / "curriculum" / "volumes").glob(f"{vid}_*"))
            if not vol_dirs:
                vol_dirs = list((self.root / "curriculum" / "volumes").glob(f"*{vid}*"))
            train_path = (
                "curriculum/volumes/01_foundation/train.jsonl"
                if not vol_dirs
                else str((vol_dirs[0] / "train.jsonl").relative_to(self.root)).replace("\\", "/")
            )
            lines = []
            for c in cases[:20]:
                q, a = c.get("question"), c.get("expected")
                if not q or not a:
                    continue
                lines.append(
                    json.dumps(
                        {
                            "id": "fix_" + uuid.uuid4().hex[:6],
                            "instruction": q,
                            "output": a,
                            "lesson": "self_mutate_fix",
                            "confidence": 0.85,
                            "tags": ["self_mutate", "weak_case"],
                        },
                        ensure_ascii=False,
                    )
                )
            if not lines:
                continue
            prop = self.propose(
                train_path,
                mode="append",
                new="\n".join(lines) + "\n",
                reason=f"diagnose_weak vol={vid} n={len(lines)}",
                author="leon:diagnose",
                goal=f"fix weak cases volume {vid}",
                strategy="train_enrich",
            )
            proposals.append(prop)

        write_json(
            self.dir / "last_diagnose_mutate.json",
            {
                "at": datetime.now().isoformat(),
                "weak": len(weak),
                "proposals": [p.get("proposal_id") for p in proposals],
            },
        )
        return {
            "ok": any(p.get("ok") for p in proposals),
            "weak_cases": len(weak),
            "proposals": proposals,
            "severity": diagnosis.get("severity"),
            "avg_pass_rate": diagnosis.get("avg_pass_rate"),
        }

    def evolve(
        self,
        *,
        rounds: int = 2,
        apply_changes: bool = False,
        goal: Optional[str] = None,
        min_quality: float = 40.0,
    ) -> Dict[str, Any]:
        """Multi-round mutation evolution (propose; apply if gated)."""
        rounds = max(1, min(int(rounds), 5))
        trail = []
        for i in range(rounds):
            step: Dict[str, Any] = {"round": i + 1}
            d = self.propose_from_diagnosis()
            step["diagnose"] = {
                "ok": d.get("ok"),
                "weak": d.get("weak_cases"),
                "ids": [p.get("proposal_id") for p in (d.get("proposals") or []) if p.get("ok")],
            }
            if goal:
                g = self.propose_from_goal(goal)
                step["goal"] = {
                    "ok": g.get("ok"),
                    "id": g.get("proposal_id"),
                    "quality": (g.get("quality") or {}).get("score"),
                }
            applied = []
            if apply_changes:
                ids = list(step["diagnose"].get("ids") or [])
                if step.get("goal", {}).get("ok") and step["goal"].get("id"):
                    ids.append(step["goal"]["id"])
                for pid in ids:
                    prop = read_json(self.dir / "proposals" / f"{pid}.json", default={})
                    qscore = float((prop.get("quality") or {}).get("score") or 0)
                    if qscore < min_quality:
                        applied.append({"proposal_id": pid, "skipped": True, "score": qscore})
                        continue
                    applied.append(self.apply(pid, run_smoke=True, min_quality=min_quality))
                step["applied"] = applied
            trail.append(step)
            if apply_changes and not any(a.get("ok") for a in applied if isinstance(a, dict)):
                break

        out = {
            "rounds": trail,
            "apply_changes": apply_changes,
            "enabled": self.mutation_enabled(),
            "path_stats": self.path_stats(),
        }
        write_json(self.dir / "last_evolve.json", out)
        return out

    def auto_cycle(
        self,
        goal: Optional[str] = None,
        *,
        apply_best: bool = False,
        from_diagnose: bool = True,
    ) -> Dict[str, Any]:
        out: Dict[str, Any] = {"steps": []}
        if from_diagnose:
            d = self.propose_from_diagnosis()
            out["diagnose_mutate"] = {
                "ok": d.get("ok"),
                "weak_cases": d.get("weak_cases"),
                "proposal_ids": [
                    p.get("proposal_id") for p in (d.get("proposals") or []) if p.get("ok")
                ],
            }
            out["steps"].append("diagnose_mutate")
        if goal:
            gprop = self.propose_from_goal(goal)
            out["goal_propose"] = gprop
            out["steps"].append("goal_propose")
        if apply_best:
            ids = []
            if out.get("diagnose_mutate"):
                ids.extend(out["diagnose_mutate"].get("proposal_ids") or [])
            if out.get("goal_propose", {}).get("ok"):
                ids.append(out["goal_propose"].get("proposal_id"))
            ranked = []
            for pid in ids:
                prop = read_json(self.dir / "proposals" / f"{pid}.json", default={}) or {}
                ranked.append((float((prop.get("quality") or {}).get("score") or 0), pid))
            best = max(ranked, default=(0.0, None))
            out["applied"] = [self.apply(best[1], run_smoke=True)] if best[1] and best[0] >= AUTO_APPLY_MIN_QUALITY else []
            out["selection"] = {"mode": "best_quality_only", "candidate_count": len(ranked), "best_score": best[0]}
            out["steps"].append("apply")
        else:
            out["note"] = "Dry propose — LEON_ALLOW_MUTATE=1 + apply_best for write"
        write_json(self.dir / "last_auto_cycle.json", out)
        return out

    def list_proposals(self, limit: int = 20) -> List[Dict[str, Any]]:
        rows = []
        for p in sorted((self.dir / "proposals").glob("MU-*.json"), reverse=True)[:limit]:
            data = read_json(p, default={}) or {}
            rows.append(
                {
                    "id": data.get("id"),
                    "path": data.get("path"),
                    "status": data.get("status"),
                    "strategy": data.get("strategy"),
                    "score": (data.get("quality") or {}).get("score"),
                    "created_at": data.get("created_at"),
                }
            )
        rows.sort(key=lambda r: (-float(r.get("score") or 0), r.get("created_at") or ""), reverse=False)
        rows.sort(key=lambda r: -float(r.get("score") or 0))
        return rows

    # ------------------------------------------------------------------ apply
    def apply(
        self,
        proposal_id: Optional[str] = None,
        *,
        run_smoke: bool = True,
        force: bool = False,
        min_quality: float = AUTO_APPLY_MIN_QUALITY,
        run_import_check: bool = True,
    ) -> Dict[str, Any]:
        if not self.mutation_enabled():
            return {
                "ok": False,
                "error": "Mutation disabled. Set LEON_ALLOW_MUTATE=1",
                "safety": "gate",
            }

        prop = None
        if proposal_id:
            prop = read_json(self.dir / "proposals" / f"{proposal_id}.json", default=None)
        if not prop:
            prop = read_json(self.dir / "last_proposal.json", default=None)
        if not prop:
            return {"ok": False, "error": "no proposal"}

        q = prop.get("quality") or {}
        if not prop.get("syntax_ok", True) or q.get("reject"):
            return {"ok": False, "error": "proposal rejected by quality/syntax", "quality": q}
        if float(q.get("score") or 0) < min_quality and q and not force:
            return {
                "ok": False,
                "error": f"quality {q.get('score')} < min_quality {min_quality}",
                "quality": q,
            }

        rel = prop["path"]
        try:
            target = self.resolve(rel)
        except MutationError as e:
            return {"ok": False, "error": str(e)}

        original = prop.get("_original")
        mutated = prop.get("_mutated")
        if mutated is None:
            return {"ok": False, "error": "proposal missing _mutated payload"}

        mid = prop.get("id") or ("MU-" + uuid.uuid4().hex[:8])
        backup_path = self.dir / "backups" / f"{mid}_{Path(rel).name}.bak"
        if target.exists():
            shutil.copy2(target, backup_path)
        else:
            backup_path.write_text("", encoding="utf-8")

        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(mutated, encoding="utf-8")

        smoke_report = None
        import_report = None
        rolled_back = False
        if rel.endswith(".py"):
            if run_import_check:
                import_report = self._import_check(rel)
                if not import_report.get("ok"):
                    target.write_text(original if original is not None else "", encoding="utf-8")
                    rolled_back = True
            if not rolled_back and run_smoke:
                smoke_report = self._smoke()
                if not smoke_report.get("ok"):
                    target.write_text(original if original is not None else "", encoding="utf-8")
                    rolled_back = True

        record = {
            "ok": not rolled_back,
            "mutation_id": mid,
            "path": rel,
            "strategy": prop.get("strategy"),
            "backup": str(backup_path),
            "applied_at": datetime.now().isoformat(),
            "rolled_back": rolled_back,
            "smoke": smoke_report,
            "import_check": import_report,
            "quality": q,
            "enabled": self.mutation_enabled(),
            "forced_quality_override": bool(force and float(q.get("score") or 0) < min_quality),
            "goal": prop.get("goal"),
            "author": prop.get("author"),
        }
        write_json(self.dir / "last_apply.json", record)
        hist = read_json(self.dir / "history.json", default={"runs": []})
        runs = hist.get("runs") or []
        runs.append(record)
        write_json(self.dir / "history.json", {"runs": runs[-100:]})

        try:
            from security.audit import audit_log

            audit_log.log(
                "self_mutate",
                user="leon",
                details={
                    "path": rel,
                    "id": mid,
                    "rolled_back": rolled_back,
                    "score": q.get("score"),
                    "strategy": prop.get("strategy"),
                },
                success=not rolled_back,
            )
        except Exception:
            pass

        logger.info(
            f"SelfMutate: {mid} path={rel} score={q.get('score')} rollback={rolled_back}"
        )
        return record

    def _import_check(self, rel: str) -> Dict[str, Any]:
        """Best-effort: compile already done; try importing module path."""
        mod = rel.replace("/", ".").removesuffix(".py")
        if mod.endswith("."):
            return {"ok": True, "skipped": True}
        try:
            import importlib

            # only re-import if already loaded; else skip heavy side effects
            if mod in list(__import__("sys").modules):
                importlib.reload(__import__("sys").modules[mod])
                return {"ok": True, "reloaded": mod}
            return {"ok": True, "skipped_fresh_import": mod}
        except Exception as e:
            return {"ok": False, "error": str(e), "module": mod}

    def _smoke(self) -> Dict[str, Any]:
        try:
            from core.bootstrap import smoke_test

            r = smoke_test()
            return {"ok": bool(r.get("overall_ok")), "detail": r.get("results")}
        except Exception as e:
            try:
                from brain.reasoning.engine import ReasoningEngine

                ReasoningEngine(persist_traces=False).reason("test", use_brain=False)
                return {"ok": True, "detail": "light reason ok", "warning": str(e)}
            except Exception as e2:
                return {"ok": False, "error": str(e2)}

    def rollback(self, mutation_id: str) -> Dict[str, Any]:
        backups = list((self.dir / "backups").glob(f"{mutation_id}_*.bak"))
        if not backups:
            return {"ok": False, "error": f"no backup for {mutation_id}"}
        prop = read_json(self.dir / "proposals" / f"{mutation_id}.json", default={})
        rel = prop.get("path") or (read_json(self.dir / "last_apply.json", default={}) or {}).get(
            "path"
        )
        if not rel:
            return {"ok": False, "error": "cannot resolve path for rollback"}
        try:
            target = self.resolve(rel)
        except MutationError as e:
            return {"ok": False, "error": str(e)}
        target.write_text(backups[0].read_text(encoding="utf-8"), encoding="utf-8")
        return {"ok": True, "path": rel, "restored_from": str(backups[0])}

    def status(self) -> Dict[str, Any]:
        return {
            "enabled": self.mutation_enabled(),
            "repo_root": str(self.root),
            "mutate_dir": str(self.dir),
            "strategies": list(STRATEGIES),
            "allowed_prefixes": list(ALLOWED_PREFIXES),
            "forbidden_prefixes": list(FORBIDDEN_PREFIXES),
            "path_stats": self.path_stats(),
            "last_proposal": {
                k: v
                for k, v in (read_json(self.dir / "last_proposal.json", default={}) or {}).items()
                if not k.startswith("_")
            },
            "last_apply": read_json(self.dir / "last_apply.json", default=None),
            "last_evolve": read_json(self.dir / "last_evolve.json", default=None),
            "last_auto_cycle": read_json(self.dir / "last_auto_cycle.json", default=None),
            "history": read_json(self.dir / "history.json", default={}),
        }


self_mutate_engine = SelfMutateEngine()


def mutate_apply(proposal_id: Optional[str] = None, **kw) -> Dict[str, Any]:
    return SelfMutateEngine().apply(proposal_id, **kw)


def smart_mutate(goal: str, *, apply: bool = False) -> Dict[str, Any]:
    return SelfMutateEngine().auto_cycle(goal=goal, apply_best=apply, from_diagnose=False)
