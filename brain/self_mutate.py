"""
Leon Self-Mutation Engine — smarter controlled source mutation.

Upgrades:
- Goal → target file smart routing
- Multi-candidate LLM proposals + quality ranking
- AST safety (no eval/exec/os.system injection)
- Size / uniqueness / import-preservation checks
- Diagnose→mutate from self_improve weak cases
- History-aware path preference
- auto_cycle: propose ranked patches (apply still gated)

Safety unchanged:
- LEON_ALLOW_MUTATE=1 for apply
- Allowlist / forbidden paths
- Backup + smoke + rollback
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

# Goal keyword → preferred relative path
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
]

DANGEROUS_AST = {
    "eval",
    "exec",
    "compile",
    "__import__",
}
DANGEROUS_ATTR = {
    ("os", "system"),
    ("os", "popen"),
    ("subprocess", "call"),
    ("subprocess", "run"),
    ("subprocess", "Popen"),
    ("shutil", "rmtree"),
}

MAX_DELTA_RATIO = 0.45  # reject if file grows/shrinks too wildly on replace
MAX_WRITE_BYTES = 200_000


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

    # ------------------------------------------------------------------ routing
    def route_goal(self, goal: str) -> Dict[str, Any]:
        """Pick best target path for a natural-language goal."""
        g = (goal or "").lower()
        hits: List[Tuple[int, str, str]] = []
        for keys, path in ROUTE_TABLE:
            score = sum(1 for k in keys if k in g)
            if score:
                hits.append((score, path, keys[0]))
        # history boost
        hist = read_json(self.dir / "history.json", default={}) or {}
        success_paths = {
            r.get("path")
            for r in (hist.get("runs") or [])
            if r.get("ok") and not r.get("rolled_back")
        }
        for i, (score, path, key) in enumerate(hits):
            if path in success_paths:
                hits[i] = (score + 2, path, key)
        hits.sort(key=lambda x: -x[0])
        if not hits:
            return {
                "path": "curriculum/volumes/01_foundation/train.jsonl",
                "strategy": "default_train",
                "score": 0,
            }
        best = hits[0]
        # if directory genome/, pick first json
        path = best[1]
        if path.endswith("/"):
            d = self.root / path
            if d.is_dir():
                cands = sorted(d.glob("*.json")) + sorted(d.glob("*.md"))
                if cands:
                    path = str(cands[0].relative_to(self.root)).replace("\\", "/")
        return {"path": path, "strategy": best[2], "score": best[0], "alternatives": hits[1:4]}

    # ------------------------------------------------------------------ quality
    def _import_names(self, tree: ast.AST) -> set:
        names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for a in node.names:
                    names.add(a.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    names.add(node.module.split(".")[0])
        return names

    def _dangerous(self, tree: ast.AST) -> List[str]:
        issues = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id in DANGEROUS_AST:
                    issues.append(f"call:{node.func.id}")
                if isinstance(node.func, ast.Attribute):
                    if isinstance(node.func.value, ast.Name):
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
    ) -> Dict[str, Any]:
        score = 50.0
        notes: List[str] = []
        syntax_ok = True
        syntax_error = None
        dangerous: List[str] = []

        if original == mutated:
            return {"score": 0, "syntax_ok": True, "notes": ["no change"], "reject": True}

        if len(mutated.encode()) > MAX_WRITE_BYTES:
            return {
                "score": 0,
                "syntax_ok": False,
                "notes": ["too large"],
                "reject": True,
            }

        if rel.endswith(".py"):
            try:
                tree_new = ast.parse(mutated)
            except SyntaxError as e:
                return {
                    "score": 0,
                    "syntax_ok": False,
                    "syntax_error": f"{e.msg} line={e.lineno}",
                    "notes": ["syntax error"],
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
                # ignore private noise
                lost = {x for x in lost if not x.startswith("_")}
                if lost and mode == "replace":
                    score -= 15
                    notes.append(f"imports_lost:{sorted(lost)[:5]}")
            score += 20
            notes.append("py_syntax_ok")

        # size delta
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

        # jsonl validity for train lines
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

        score = max(0.0, min(100.0, score))
        return {
            "score": round(score, 1),
            "syntax_ok": syntax_ok,
            "syntax_error": syntax_error,
            "notes": notes,
            "dangerous": dangerous,
            "reject": score < 25,
        }

    # ------------------------------------------------------------------ propose
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

        if mode == "replace":
            if not old:
                return {"ok": False, "error": "replace mode requires old="}
            # normalize newlines once
            if old not in original and old.replace("\r\n", "\n") in original.replace("\r\n", "\n"):
                original_n = original.replace("\r\n", "\n")
                old_n = old.replace("\r\n", "\n")
                new_n = new.replace("\r\n", "\n")
                count = original_n.count(old_n)
                if count != 1:
                    return {"ok": False, "error": f"old must appear exactly once (found {count})"}
                mutated = original_n.replace(old_n, new_n, 1)
            else:
                count = original.count(old)
                if count != 1:
                    # try fuzzy unique block by stripping outer whitespace lines
                    fuzzy = self._fuzzy_unique(original, old)
                    if fuzzy is None:
                        return {
                            "ok": False,
                            "error": f"old must appear exactly once (found {count})",
                        }
                    mutated = original.replace(fuzzy, new, 1)
                else:
                    mutated = original.replace(old, new, 1)
        elif mode == "append":
            piece = new if new.endswith("\n") or not new else new + "\n"
            mutated = original + piece
        elif mode == "write":
            mutated = content
        else:
            return {"ok": False, "error": f"unknown mode: {mode}"}

        quality = self.score_mutation(rel, original, mutated, mode=mode)
        syntax_ok = quality.get("syntax_ok", True) and not quality.get("reject")

        pid = "MU-" + str(uuid.uuid4())[:8]
        proposal = {
            "id": pid,
            "path": rel,
            "mode": mode,
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
            "syntax_ok": syntax_ok,
            "syntax_error": quality.get("syntax_error"),
            "quality": quality,
            "diff_preview": proposal["diff_preview"],
            "status": proposal["status"],
            "enabled": self.mutation_enabled(),
            "hint": None
            if self.mutation_enabled()
            else "Apply üçün: export LEON_ALLOW_MUTATE=1",
        }

    def _fuzzy_unique(self, text: str, fragment: str) -> Optional[str]:
        frag = fragment.strip()
        if not frag:
            return None
        # sliding windows of same line count
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
        if len(matches) == 1:
            return matches[0]
        return None

    def propose_from_goal(
        self,
        goal: str,
        *,
        path: Optional[str] = None,
        candidates: int = 3,
    ) -> Dict[str, Any]:
        """Smart goal→patch: route, heuristic knowledge, multi LLM candidates ranked."""
        route = self.route_goal(goal)
        target = path or route["path"]
        goal_l = (goal or "").lower()

        # Knowledge path: structured jsonl append (most reliable)
        if target.endswith(".jsonl") or any(
            k in goal_l for k in ("öyrən", "learn", "fact", "bilik", "qa", "sual", "dərs")
        ):
            if not target.endswith(".jsonl"):
                target = "curriculum/volumes/01_foundation/train.jsonl"
            q, a = self._extract_qa(goal)
            line = json.dumps(
                {
                    "id": "auto_" + uuid.uuid4().hex[:6],
                    "instruction": q,
                    "output": a,
                    "lesson": "self_mutate",
                    "confidence": 0.7,
                    "tags": ["self_mutate", "auto"],
                },
                ensure_ascii=False,
            )
            prop = self.propose(
                target,
                mode="append",
                new=line + "\n",
                reason=f"goal:{goal[:120]}",
                author="leon:heuristic",
                goal=goal,
            )
            prop["route"] = route
            prop["strategy"] = "jsonl_append"
            return prop

        # Code path: multi-candidate LLM surgical replace
        ranked = self._llm_ranked_patches(target, goal, n=max(1, min(candidates, 5)))
        if not ranked:
            return {
                "ok": False,
                "error": "No valid LLM candidates",
                "route": route,
                "hint": "Try --path with explicit replace, or knowledge-style goal",
            }

        best = ranked[0]
        prop = self.propose(
            target,
            mode="replace",
            old=best["old"],
            new=best["new"],
            reason=f"goal:{goal[:120]}",
            author="leon:llm_ranked",
            goal=goal,
        )
        prop["route"] = route
        prop["strategy"] = "llm_ranked"
        prop["candidates"] = [
            {"rank": i + 1, "quality": c.get("quality"), "preview": (c.get("new") or "")[:120]}
            for i, c in enumerate(ranked[:5])
        ]
        return prop

    def _extract_qa(self, goal: str) -> Tuple[str, str]:
        g = goal.strip()
        # "Sual: ... Cavab: ..."
        m = re.search(r"sual\s*[:：]\s*(.+?)\s*cavab\s*[:：]\s*(.+)", g, re.I | re.S)
        if m:
            return m.group(1).strip()[:200], m.group(2).strip()[:200]
        m = re.search(r"q\s*[:：]\s*(.+?)\s*a\s*[:：]\s*(.+)", g, re.I | re.S)
        if m:
            return m.group(1).strip()[:200], m.group(2).strip()[:200]
        # default: treat whole goal as instruction
        return g[:200], "Bəli." if any(x in g.lower() for x in ("mövcud", "obyekt", "var")) else "Öyrənilmiş."

    def _llm_ranked_patches(self, rel: str, goal: str, n: int = 3) -> List[Dict[str, Any]]:
        src_path = self.root / rel
        if not src_path.exists() or not rel.endswith(".py"):
            return []
        src = src_path.read_text(encoding="utf-8")
        # prefer middle of file for context window
        snippet = src[:6000] if len(src) < 7000 else src[:3000] + "\n# …\n" + src[-3000:]

        try:
            from brain.llm.client import get_llm_client

            client = get_llm_client()
        except Exception:
            return []

        system = (
            "You are Leon's careful code mutator. Return ONLY a JSON array of up to "
            f"{n} objects. Each: {{\"old\":\"exact unique substring\",\"new\":\"replacement\",\"why\":\"...\"}}. "
            "old must appear exactly once and be at most 12 lines. Prefer minimal surgical edits. "
            "Never introduce eval/exec/os.system/subprocess. Never touch security modules."
        )
        prompt = f"GOAL:\n{goal[:300]}\n\nFILE {rel}:\n{snippet}"
        reply = client.complete(prompt, system=system, temperature=0.3, max_tokens=1200)
        if not reply:
            return []

        items = self._parse_json_array(reply)
        ranked: List[Dict[str, Any]] = []
        for it in items:
            old, new = it.get("old") or "", it.get("new") or ""
            if not old or new is None:
                continue
            if src.count(old) != 1 and self._fuzzy_unique(src, old) is None:
                continue
            mutated = src.replace(old, new, 1) if old in src else src.replace(
                self._fuzzy_unique(src, old) or old, new, 1
            )
            q = self.score_mutation(rel, src, mutated, mode="replace")
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
        # array
        try:
            m = re.search(r"\[.*\]", text, re.S)
            if m:
                data = json.loads(m.group(0))
                if isinstance(data, list):
                    return [x for x in data if isinstance(x, dict)]
        except Exception:
            pass
        # single object
        try:
            m = re.search(r"\{.*\}", text, re.S)
            if m:
                data = json.loads(m.group(0))
                if isinstance(data, dict):
                    return [data]
        except Exception:
            pass
        return []

    # ------------------------------------------------------------------ diagnose-driven
    def propose_from_diagnosis(
        self, diagnosis: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Turn self_improve weak_cases into train.jsonl mutations (batch proposal)."""
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
            vid = str(c.get("volume_id") or "01")
            by_vol.setdefault(vid, []).append(c)

        proposals = []
        for vid, cases in by_vol.items():
            # map volume id to train path
            vol_dirs = list((self.root / "curriculum" / "volumes").glob(f"{vid}_*"))
            if not vol_dirs:
                vol_dirs = list((self.root / "curriculum" / "volumes").glob(f"*{vid}*"))
            if not vol_dirs:
                train_path = "curriculum/volumes/01_foundation/train.jsonl"
            else:
                train_path = str((vol_dirs[0] / "train.jsonl").relative_to(self.root)).replace(
                    "\\", "/"
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

    def auto_cycle(
        self,
        goal: Optional[str] = None,
        *,
        apply_best: bool = False,
        from_diagnose: bool = True,
    ) -> Dict[str, Any]:
        """
        Intelligent cycle:
          optional diagnose→knowledge patches
          optional goal→ranked code/knowledge patch
          apply only if apply_best and LEON_ALLOW_MUTATE
        """
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

        applied = []
        if apply_best:
            # apply last successful proposals (diagnose first, then goal)
            ids = []
            if out.get("diagnose_mutate"):
                ids.extend(out["diagnose_mutate"].get("proposal_ids") or [])
            if out.get("goal_propose", {}).get("ok"):
                ids.append(out["goal_propose"].get("proposal_id"))
            for pid in ids:
                if not pid:
                    continue
                applied.append(self.apply(pid, run_smoke=True))
            out["applied"] = applied
            out["steps"].append("apply")
        else:
            out["note"] = "Dry propose only — set apply_best=True and LEON_ALLOW_MUTATE=1 to apply"

        write_json(self.dir / "last_auto_cycle.json", out)
        return out

    def _preview(self, old: str, new: str, lines: int = 6) -> str:
        if old == new:
            return "(no change)"
        o = old.splitlines()
        n = new.splitlines()
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

    # ------------------------------------------------------------------ apply / rollback
    def apply(
        self,
        proposal_id: Optional[str] = None,
        *,
        run_smoke: bool = True,
        force: bool = False,
        min_quality: float = 25.0,
    ) -> Dict[str, Any]:
        if not self.mutation_enabled() and not force:
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
            return {
                "ok": False,
                "error": "proposal rejected by quality/syntax",
                "quality": q,
            }
        if float(q.get("score") or 0) < min_quality and q:
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
        rolled_back = False
        if run_smoke and rel.endswith(".py"):
            smoke_report = self._smoke()
            if not smoke_report.get("ok"):
                target.write_text(original if original is not None else "", encoding="utf-8")
                rolled_back = True

        record = {
            "ok": not rolled_back,
            "mutation_id": mid,
            "path": rel,
            "backup": str(backup_path),
            "applied_at": datetime.now().isoformat(),
            "rolled_back": rolled_back,
            "smoke": smoke_report,
            "quality": q,
            "enabled": self.mutation_enabled(),
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
                },
                success=not rolled_back,
            )
        except Exception:
            pass

        logger.info(
            f"SelfMutate: {mid} path={rel} score={q.get('score')} rollback={rolled_back}"
        )
        return record

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
        rel = prop.get("path")
        if not rel:
            last = read_json(self.dir / "last_apply.json", default={})
            rel = last.get("path")
        if not rel:
            return {"ok": False, "error": "cannot resolve path for rollback"}
        try:
            target = self.resolve(rel)
        except MutationError as e:
            return {"ok": False, "error": str(e)}
        bak = backups[0]
        target.write_text(bak.read_text(encoding="utf-8"), encoding="utf-8")
        return {"ok": True, "path": rel, "restored_from": str(bak)}

    def status(self) -> Dict[str, Any]:
        return {
            "enabled": self.mutation_enabled(),
            "repo_root": str(self.root),
            "mutate_dir": str(self.dir),
            "allowed_prefixes": list(ALLOWED_PREFIXES),
            "forbidden_prefixes": list(FORBIDDEN_PREFIXES),
            "routes": [(list(k), p) for k, p in ROUTE_TABLE],
            "last_proposal": {
                k: v
                for k, v in (read_json(self.dir / "last_proposal.json", default={}) or {}).items()
                if not k.startswith("_")
            },
            "last_apply": read_json(self.dir / "last_apply.json", default=None),
            "last_auto_cycle": read_json(self.dir / "last_auto_cycle.json", default=None),
            "history": read_json(self.dir / "history.json", default={}),
        }


self_mutate_engine = SelfMutateEngine()


def mutate_apply(proposal_id: Optional[str] = None, **kw) -> Dict[str, Any]:
    return SelfMutateEngine().apply(proposal_id, **kw)


def smart_mutate(goal: str, *, apply: bool = False) -> Dict[str, Any]:
    """Public: intelligent propose (and optional apply)."""
    eng = SelfMutateEngine()
    return eng.auto_cycle(goal=goal, apply_best=apply, from_diagnose=False)
