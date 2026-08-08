"""
Leon Self-View — body awareness / introspection.

Leon can see organs (cells), modules, lines, AST symbols, search own code.
Write path remains gated.
"""

from __future__ import annotations

import ast
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.persistence import write_json


SKIP_DIRS = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    "node_modules",
    ".mypy_cache",
    ".pytest_cache",
    "dist",
    "build",
    ".eggs",
}

ORGANS = {
    "brain": "cognitive_core",
    "core": "vital_organs",
    "knowledge": "long_term_memory_store",
    "memory": "working_memory_tissue",
    "learning": "plasticity",
    "curriculum": "education",
    "agents": "effectors",
    "tools": "hands",
    "multimodal": "senses",
    "security": "immune_system",
    "interfaces": "skin_api",
    "evaluation": "self_test",
    "genome": "genome",
    "schemas": "blueprints",
    "integrations": "external_nerves",
    "training": "muscle_training",
    "models": "model_tissue",
    "inference": "reflex_arc",
    "docs": "documentation",
    "tests": "immune_assays",
    "scripts": "maintenance",
    "data": "body_state",
    "utils": "utilities",
}


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


class SelfView:
    def __init__(self, repo_root: Optional[Path] = None):
        self.root = Path(repo_root) if repo_root else _repo_root()

    def map(self, *, include_lines: bool = True) -> Dict[str, Any]:
        cells: Dict[str, Dict[str, Any]] = {}
        total_py = 0
        total_lines = 0
        for organ, role in ORGANS.items():
            d = self.root / organ
            if not d.is_dir():
                continue
            modules = []
            organ_lines = 0
            for p in sorted(d.rglob("*.py")):
                if any(part in SKIP_DIRS for part in p.parts):
                    continue
                rel = str(p.relative_to(self.root)).replace("\\", "/")
                try:
                    text = p.read_text(encoding="utf-8", errors="replace")
                    nlines = text.count("\n") + (1 if text and not text.endswith("\n") else 0)
                except Exception:
                    nlines = 0
                organ_lines += nlines
                total_lines += nlines
                total_py += 1
                modules.append(
                    {
                        "path": rel,
                        "lines": nlines if include_lines else None,
                        "mutable": self.mutability(rel)["mutable"],
                    }
                )
            cells[organ] = {
                "role": role,
                "module_count": len(modules),
                "lines": organ_lines,
                "modules": modules,
            }

        out = {
            "identity": "Leon",
            "repo_root": str(self.root),
            "at": datetime.now().isoformat(),
            "summary": {
                "organs": len(cells),
                "python_modules": total_py,
                "approx_lines": total_lines,
            },
            "cells": cells,
            "note": "Write: LEON_ALLOW_MUTATE + allowlist + green-gate. Read: unrestricted within repo.",
        }
        try:
            from core.config import config

            d = Path(config.path.leon_dir) / "self_view"
        except Exception:
            d = Path("data/leon/self_view")
        d.mkdir(parents=True, exist_ok=True)
        write_json(d / "last_map.json", out)
        return out

    def cell(self, name: str) -> Dict[str, Any]:
        name = (name or "").strip().strip("/")
        d = self.root / name
        if not d.exists():
            return {"ok": False, "error": f"unknown cell: {name}"}
        files = []
        for p in sorted(d.rglob("*")):
            if p.is_dir() or any(part in SKIP_DIRS for part in p.parts):
                continue
            rel = str(p.relative_to(self.root)).replace("\\", "/")
            try:
                text = p.read_text(encoding="utf-8", errors="replace")
                nlines = text.count("\n") + 1
            except Exception:
                nlines = 0
            files.append(
                {
                    "path": rel,
                    "lines": nlines,
                    "suffix": p.suffix,
                    "mutable": self.mutability(rel)["mutable"] if p.suffix == ".py" else False,
                }
            )
        return {
            "ok": True,
            "cell": name,
            "role": ORGANS.get(name.split("/")[0], "tissue"),
            "file_count": len(files),
            "files": files,
        }

    def read(
        self,
        path: str,
        *,
        start: int = 1,
        end: Optional[int] = None,
        max_lines: int = 200,
    ) -> Dict[str, Any]:
        rel = path.replace("\\", "/").lstrip("./")
        target = (self.root / rel).resolve()
        try:
            target.relative_to(self.root.resolve())
        except ValueError:
            return {"ok": False, "error": "path escapes repo"}
        if not target.exists() or not target.is_file():
            return {"ok": False, "error": f"missing: {rel}"}

        lines = target.read_text(encoding="utf-8", errors="replace").splitlines()
        start = max(1, int(start))
        if end is None:
            end = start + max_lines - 1
        end = min(len(lines), max(start, int(end)))
        if end - start + 1 > max_lines:
            end = start + max_lines - 1
        window = [{"n": i, "text": lines[i - 1]} for i in range(start, end + 1)]
        return {
            "ok": True,
            "path": rel,
            "total_lines": len(lines),
            "start": start,
            "end": end,
            "lines": window,
            "mutable": self.mutability(rel),
        }

    def symbols(self, path: str) -> Dict[str, Any]:
        rel = path.replace("\\", "/").lstrip("./")
        target = self.root / rel
        if not target.exists():
            return {"ok": False, "error": f"missing: {rel}"}
        src = target.read_text(encoding="utf-8", errors="replace")
        try:
            tree = ast.parse(src)
        except SyntaxError as e:
            return {"ok": False, "error": f"syntax: {e.msg}:{e.lineno}"}

        classes = []
        functions = []
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                methods = [
                    {"name": n.name, "lineno": n.lineno}
                    for n in node.body
                    if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                ]
                classes.append({"name": node.name, "lineno": node.lineno, "methods": methods})
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                functions.append({"name": node.name, "lineno": node.lineno})

        return {
            "ok": True,
            "path": rel,
            "classes": classes,
            "functions": functions,
            "mutable": self.mutability(rel),
        }

    def search(
        self, query: str, *, path_prefix: str = "", max_hits: int = 40
    ) -> Dict[str, Any]:
        q = (query or "").strip()
        if not q:
            return {"ok": False, "error": "empty query"}
        hits = []
        root = self.root / path_prefix if path_prefix else self.root
        for p in root.rglob("*.py"):
            if any(part in SKIP_DIRS for part in p.parts):
                continue
            try:
                text = p.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue
            for i, line in enumerate(text.splitlines(), 1):
                if q.lower() in line.lower():
                    hits.append(
                        {
                            "path": str(p.relative_to(self.root)).replace("\\", "/"),
                            "line": i,
                            "text": line.strip()[:200],
                        }
                    )
                    if len(hits) >= max_hits:
                        return {"ok": True, "query": q, "hits": hits, "truncated": True}
        return {"ok": True, "query": q, "hits": hits, "truncated": False}

    def mutability(self, path: str) -> Dict[str, Any]:
        rel = path.replace("\\", "/").lstrip("./")
        try:
            from brain.mutate_allowlist import ALLOWED_PREFIXES, FORBIDDEN_PREFIXES

            for bad in FORBIDDEN_PREFIXES:
                if rel.startswith(bad) or rel == bad.rstrip("/"):
                    return {"mutable": False, "reason": f"forbidden:{bad}", "apply_gate": False}
            for good in ALLOWED_PREFIXES:
                if rel.startswith(good) or rel == good.rstrip("/"):
                    try:
                        from brain.self_mutate import SelfMutateEngine

                        gate = SelfMutateEngine().mutation_enabled()
                    except Exception:
                        gate = False
                    return {"mutable": True, "reason": "allowlist", "apply_gate": gate}
            return {"mutable": False, "reason": "not in allowlist", "apply_gate": False}
        except Exception:
            try:
                from brain.self_mutate import SelfMutateEngine

                eng = SelfMutateEngine(repo_root=self.root)
                ok, reason = eng.is_allowed(path)
                return {"mutable": ok, "reason": reason, "apply_gate": eng.mutation_enabled()}
            except Exception as e:
                return {"mutable": False, "reason": str(e), "apply_gate": False}

    def body(self) -> Dict[str, Any]:
        m = self.map(include_lines=True)
        cells = {
            k: {"role": v["role"], "modules": v["module_count"], "lines": v["lines"]}
            for k, v in (m.get("cells") or {}).items()
        }
        return {
            "identity": "Leon",
            "summary": m.get("summary"),
            "cells": cells,
            "self_modules": {
                "self_view": "brain/self_view.py",
                "self_mutate": "brain/self_mutate.py",
                "self_code": "brain/self_code.py",
                "self_improve": "brain/self_improve.py",
                "code_verify": "brain/code_verify.py",
                "mutate_allowlist": "brain/mutate_allowlist.py",
            },
            "write_policy": "allowlist + LEON_ALLOW_MUTATE + green-gate; security/core/kernel forbidden",
        }


self_view = SelfView()


def body_map() -> Dict[str, Any]:
    return SelfView().body()
