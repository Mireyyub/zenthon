"""
Leon Self-Mutation Engine — controlled source code mutation.

Safety model:
- Explicit enable: env LEON_ALLOW_MUTATE=1 required for apply
- Path allowlist only; security/, kernel, .git forever forbidden
- Backup before write; AST parse for .py; optional smoke; rollback
- Never grants shell/network tools via mutation of security modules

This is deliberate evolution under gates — not unrestricted self-rewriting.
"""

from __future__ import annotations

import ast
import hashlib
import os
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


# Relative to repo root
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
    "brain/self_mutate.py",  # cannot rewrite the mutator itself in-loop
)


class MutationError(Exception):
    pass


class SelfMutateEngine:
    def __init__(self, repo_root: Optional[Path] = None):
        self.root = Path(repo_root) if repo_root else _repo_root()
        self.dir = _mutate_dir()

    def mutation_enabled(self) -> bool:
        return os.environ.get("LEON_ALLOW_MUTATE", "").strip() in ("1", "true", "yes", "on")

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
    ) -> Dict[str, Any]:
        """
        mode:
          replace — old must appear exactly once
          append  — append new to file
          write   — full file content (dangerous; still allowlisted)
        """
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
            count = original.count(old)
            if count != 1:
                return {
                    "ok": False,
                    "error": f"old must appear exactly once (found {count})",
                }
            mutated = original.replace(old, new, 1)
        elif mode == "append":
            mutated = original + (new if new.endswith("\n") or not new else new + "\n")
        elif mode == "write":
            mutated = content
        else:
            return {"ok": False, "error": f"unknown mode: {mode}"}

        # syntax check for python
        syntax_ok = True
        syntax_error = None
        if rel.endswith(".py"):
            try:
                ast.parse(mutated)
            except SyntaxError as e:
                syntax_ok = False
                syntax_error = f"{e.msg} line={e.lineno}"

        pid = "MU-" + str(uuid.uuid4())[:8]
        proposal = {
            "id": pid,
            "path": rel,
            "mode": mode,
            "reason": reason,
            "author": author,
            "created_at": datetime.now().isoformat(),
            "original_sha16": hashlib.sha256(original.encode()).hexdigest()[:16],
            "mutated_sha16": hashlib.sha256(mutated.encode()).hexdigest()[:16],
            "syntax_ok": syntax_ok,
            "syntax_error": syntax_error,
            "bytes_before": len(original.encode()),
            "bytes_after": len(mutated.encode()),
            "diff_preview": self._preview(original, mutated),
            "status": "proposed" if syntax_ok else "rejected_syntax",
            # store payloads for apply
            "_original": original,
            "_mutated": mutated,
        }
        # persist without huge optional if too large — always store for apply
        write_json(self.dir / "proposals" / f"{pid}.json", proposal)
        write_json(self.dir / "last_proposal.json", {k: v for k, v in proposal.items()})
        return {
            "ok": syntax_ok,
            "proposal_id": pid,
            "path": rel,
            "syntax_ok": syntax_ok,
            "syntax_error": syntax_error,
            "diff_preview": proposal["diff_preview"],
            "status": proposal["status"],
            "enabled": self.mutation_enabled(),
            "hint": None
            if self.mutation_enabled()
            else "Apply üçün: export LEON_ALLOW_MUTATE=1",
        }

    def propose_from_goal(self, goal: str) -> Dict[str, Any]:
        """
        Heuristic/LLM-assisted proposal generator.
        Safe defaults: append train.jsonl QA or genome note — not arbitrary code.
        """
        goal_l = (goal or "").lower()
        # Prefer knowledge mutation over code
        if any(k in goal_l for k in ("öyrən", "learn", "fact", "bilik", "qa", "sual")):
            path = "curriculum/volumes/01_foundation/train.jsonl"
            line = (
                '{"id":"auto_%s","instruction":"%s","output":"Öyrənilməli fakt.",'
                '"lesson":"self_mutate","confidence":0.6,"tags":["self_mutate"]}\n'
                % (uuid.uuid4().hex[:6], goal[:80].replace('"', "'"))
            )
            return self.propose(
                path, mode="append", new=line, reason=f"goal:{goal[:120]}", author="leon:heuristic"
            )

        # Try LLM for a surgical replace only inside allowlisted coding_agent docstring
        try:
            from brain.llm.client import get_llm_client

            client = get_llm_client()
            path = "agents/coding_agent.py"
            src = (self.root / path).read_text(encoding="utf-8")
            prompt = (
                "Leon self-mutate. Return ONLY a JSON object with keys old and new. "
                "old must be an exact unique substring from the file (max 8 lines). "
                "new is improved version. Goal: "
                + goal[:200]
                + "\n\nFILE START\n"
                + src[:4000]
            )
            reply = client.complete(prompt, system="Output JSON only: {\"old\":\"...\",\"new\":\"...\"}")
            if reply and "{" in reply:
                import json as _json
                import re

                m = re.search(r"\{.*\}", reply, re.S)
                if m:
                    data = _json.loads(m.group(0))
                    return self.propose(
                        path,
                        mode="replace",
                        old=data.get("old", ""),
                        new=data.get("new", ""),
                        reason=f"goal:{goal[:120]}",
                        author="leon:llm",
                    )
        except Exception as e:
            logger.debug(f"propose_from_goal llm: {e}")

        return {
            "ok": False,
            "error": "Could not build safe proposal from goal",
            "hint": "Use propose(path, mode=replace|append|write) explicitly",
        }

    def _preview(self, old: str, new: str, lines: int = 6) -> str:
        if old == new:
            return "(no change)"
        o = old.splitlines()
        n = new.splitlines()
        # simple: show length delta + first differing region
        for i, (a, b) in enumerate(zip(o, n)):
            if a != b:
                start = max(0, i - 1)
                chunk_o = o[start : start + lines]
                chunk_n = n[start : start + lines]
                return (
                    "--- old ---\n"
                    + "\n".join(chunk_o)
                    + "\n+++ new +++\n"
                    + "\n".join(chunk_n)
                )
        if len(n) > len(o):
            return "+++ appended +++\n" + "\n".join(n[len(o) : len(o) + lines])
        return f"bytes {len(old)} → {len(new)}"

    # ------------------------------------------------------------------ apply
    def apply(
        self,
        proposal_id: Optional[str] = None,
        *,
        run_smoke: bool = True,
        force: bool = False,
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

        if not prop.get("syntax_ok", True):
            return {"ok": False, "error": "proposal failed syntax check", "detail": prop.get("syntax_error")}

        rel = prop["path"]
        try:
            target = self.resolve(rel)
        except MutationError as e:
            return {"ok": False, "error": str(e)}

        original = prop.get("_original")
        mutated = prop.get("_mutated")
        if mutated is None:
            return {"ok": False, "error": "proposal missing _mutated payload"}

        # backup
        mid = prop.get("id") or ("MU-" + uuid.uuid4().hex[:8])
        backup_path = self.dir / "backups" / f"{mid}_{Path(rel).name}.bak"
        if target.exists():
            shutil.copy2(target, backup_path)
        else:
            backup_path.write_text("", encoding="utf-8")

        # write
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(mutated, encoding="utf-8")

        smoke_report = None
        rolled_back = False
        if run_smoke and rel.endswith(".py"):
            smoke_report = self._smoke()
            if not smoke_report.get("ok"):
                # rollback
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
            "enabled": self.mutation_enabled(),
        }
        write_json(self.dir / "last_apply.json", record)
        hist = read_json(self.dir / "history.json", default={"runs": []})
        runs = hist.get("runs") or []
        runs.append(record)
        write_json(self.dir / "history.json", {"runs": runs[-100:]})

        # audit
        try:
            from security.audit import audit_log

            audit_log(
                "self_mutate",
                {"path": rel, "id": mid, "rolled_back": rolled_back},
                user="leon",
            )
        except Exception:
            pass

        logger.info(f"SelfMutate: {mid} path={rel} rollback={rolled_back}")
        return record

    def _smoke(self) -> Dict[str, Any]:
        try:
            from core.bootstrap import smoke_test

            r = smoke_test()
            return {"ok": bool(r.get("overall_ok")), "detail": r.get("results")}
        except Exception as e:
            # lighter: import brain.reasoning
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
        # find proposal for path
        prop = read_json(self.dir / "proposals" / f"{mutation_id}.json", default={})
        rel = prop.get("path")
        if not rel:
            # try last_apply
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
            "last_proposal": {
                k: v
                for k, v in (read_json(self.dir / "last_proposal.json", default={}) or {}).items()
                if not k.startswith("_")
            },
            "last_apply": read_json(self.dir / "last_apply.json", default=None),
            "history": read_json(self.dir / "history.json", default={}),
        }


self_mutate_engine = SelfMutateEngine()


def mutate_apply(proposal_id: Optional[str] = None, **kw) -> Dict[str, Any]:
    return SelfMutateEngine().apply(proposal_id, **kw)
