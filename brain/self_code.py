"""
Leon Code Author — write original code + green-gate verify.

Flow:
  generate → validate → propose/apply → code_verify → rollback if red

CREATE only under CREATE_PREFIXES; never security/core/self_mutate.
"""

from __future__ import annotations

import ast
import re
import textwrap
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from core.logger import logger
from core.persistence import write_json, read_json


CREATE_PREFIXES = (
    "brain/reasoning/",
    "agents/",
    "multimodal/",
    "learning/",
    "evaluation/",
    "memory/",
    "docs/",
)

DANGEROUS_PATTERNS = (
    r"\beval\s*\(",
    r"\bexec\s*\(",
    r"\bos\.system\s*\(",
    r"\bsubprocess\.",
    r"\b__import__\s*\(",
)


def _mutate_dir() -> Path:
    try:
        from core.config import config

        d = Path(config.path.leon_dir) / "mutations"
    except Exception:
        d = Path("data/leon/mutations")
    d.mkdir(parents=True, exist_ok=True)
    return d


class CodeAuthor:
    def __init__(self):
        from brain.self_mutate import SelfMutateEngine

        self.mut = SelfMutateEngine()
        self.dir = _mutate_dir()

    def can_create(self, rel: str) -> bool:
        rel = rel.replace("\\", "/").lstrip("./")
        for bad in ("security/", "core/", "brain/self_mutate"):
            if rel.startswith(bad):
                return False
        return any(rel.startswith(p) for p in CREATE_PREFIXES)

    def generate_function(
        self,
        spec: str,
        *,
        name: Optional[str] = None,
        use_llm: bool = True,
    ) -> Dict[str, Any]:
        fname = name or self._infer_name(spec)
        code = None
        source = "template"
        if use_llm:
            code = self._llm_function(spec, fname)
            if code:
                source = "llm"
        if not code:
            code = self._template_function(spec, fname)
            source = "template"
        check = self._validate_code(code)
        return {
            "ok": check["ok"],
            "name": fname,
            "code": code,
            "source": source,
            "validation": check,
        }

    def _infer_name(self, spec: str) -> str:
        m = re.search(r"\bdef\s+([a-zA-Z_]\w*)", spec)
        if m:
            return m.group(1)
        words = re.findall(r"[a-zA-Z]{3,}", spec.lower())
        stop = {"the", "and", "for", "that", "with", "function", "method", "leon", "write", "create"}
        parts = [w for w in words if w not in stop][:4]
        if not parts:
            return "leon_generated_" + uuid.uuid4().hex[:6]
        return "_".join(parts)[:48]

    def _template_function(self, spec: str, name: str) -> str:
        doc = spec.strip().replace('"', "'")[:200]
        return textwrap.dedent(
            f'''
            def {name}(*args, **kwargs):
                """{doc}

                Auto-authored by Leon CodeAuthor (template).
                """
                from core.logger import logger
                logger.debug("Leon generated function {name} called")
                return {{
                    "ok": True,
                    "function": "{name}",
                    "args_len": len(args),
                    "kwargs_keys": list(kwargs.keys()),
                    "note": "template implementation — refine via further mutation",
                }}
            '''
        ).strip() + "\n"

    def _llm_function(self, spec: str, name: str) -> Optional[str]:
        try:
            from brain.llm.client import get_llm_client

            client = get_llm_client()
        except Exception:
            return None
        system = (
            "You are Leon's code author. Return ONLY a complete Python function "
            f"named {name}. No markdown. No eval/exec/os.system/subprocess. "
            "Type hints preferred. Under 60 lines. Safe pure-ish logic."
        )
        reply = client.complete(
            f"Write function `{name}` that: {spec[:500]}",
            system=system,
            temperature=0.2,
            max_tokens=900,
        )
        if not reply:
            return None
        code = self._extract_python(reply)
        if f"def {name}" not in code and "def " in code:
            code = re.sub(r"def\s+[a-zA-Z_]\w*", f"def {name}", code, count=1)
        return code if "def " in code else None

    def _extract_python(self, text: str) -> str:
        text = text.strip()
        m = re.search(r"```(?:python)?\s*([\s\S]*?)```", text)
        if m:
            return m.group(1).strip() + "\n"
        return text + ("\n" if not text.endswith("\n") else "")

    def _validate_code(self, code: str) -> Dict[str, Any]:
        issues = []
        try:
            tree = ast.parse(code)
            compile(code, "<leon_codegen>", "exec")
        except SyntaxError as e:
            return {"ok": False, "error": f"syntax: {e.msg} line={e.lineno}"}
        funcs = [n for n in tree.body if isinstance(n, ast.FunctionDef)]
        if not funcs:
            issues.append("no_function")
        for pat in DANGEROUS_PATTERNS:
            if re.search(pat, code):
                issues.append(f"dangerous:{pat}")
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                if node.func.id in ("eval", "exec", "__import__"):
                    issues.append(f"call:{node.func.id}")
        return {"ok": not issues, "issues": issues, "func_count": len(funcs)}

    def insert_into_module(
        self, path: str, code: str, *, goal: str = "", apply: bool = False, verify: bool = True
    ) -> Dict[str, Any]:
        rel = path.replace("\\", "/").lstrip("./")
        ok, why = self.mut.is_allowed(rel)
        if not ok:
            return {"ok": False, "error": f"not mutable: {rel} ({why})"}
        if not rel.endswith(".py"):
            return {"ok": False, "error": "target must be .py"}

        marker = (
            "\n\n# --- Leon CodeAuthor insert "
            + datetime.now().strftime("%Y%m%d%H%M%S")
            + " ---\n"
        )
        block = marker + code.rstrip() + "\n"
        prop = self.mut.propose(
            rel,
            mode="append",
            new=block,
            reason=f"code_author:insert {goal[:80]}",
            author="leon:code_author",
            goal=goal,
            strategy="code_insert",
        )
        out: Dict[str, Any] = {"proposal": prop, "path": rel}
        if apply and prop.get("ok"):
            out["apply"] = self.mut.apply(prop.get("proposal_id"), run_smoke=True)
            if verify and out["apply"].get("ok"):
                out["verify"] = self._gate(rel, out["apply"].get("mutation_id"))
        return out

    def create_module(
        self,
        path: str,
        *,
        code: Optional[str] = None,
        spec: str = "",
        apply: bool = False,
        verify: bool = True,
    ) -> Dict[str, Any]:
        rel = path.replace("\\", "/").lstrip("./")
        if not rel.endswith(".py"):
            rel = rel.rstrip("/") + ".py"
        if not self.can_create(rel):
            return {
                "ok": False,
                "error": f"cannot create {rel}",
                "create_prefixes": list(CREATE_PREFIXES),
            }

        if code is None:
            gen = self.generate_function(spec or f"module helper for {rel}")
            if not gen.get("ok"):
                return {"ok": False, "error": "codegen failed", "detail": gen}
            body = gen["code"]
        else:
            body = code
            try:
                ast.parse(body)
                compile(body, rel, "exec")
            except SyntaxError as e:
                return {"ok": False, "error": str(e)}

        header = textwrap.dedent(
            f'''
            """Auto-authored by Leon CodeAuthor.
            Spec: {(spec or path)[:200]}
            Generated: {datetime.now().isoformat()}
            """
            from __future__ import annotations

            from core.logger import logger

            '''
        )
        full = header + body.rstrip() + "\n"

        ok_mut, _ = self.mut.is_allowed(rel)
        if not ok_mut:
            prop = self._propose_create_write(rel, full, spec=spec)
        else:
            prop = self.mut.propose(
                rel,
                mode="write",
                content=full,
                reason=f"code_author:create {spec[:80]}",
                author="leon:code_author",
                goal=spec,
                strategy="code_create",
            )

        out: Dict[str, Any] = {"proposal": prop, "path": rel, "bytes": len(full)}
        if apply and prop.get("ok"):
            if prop.get("direct_write"):
                out["apply"] = self._apply_create(rel, full, prop.get("proposal_id"))
            else:
                out["apply"] = self.mut.apply(prop.get("proposal_id"), run_smoke=True)
            if verify and out.get("apply", {}).get("ok"):
                out["verify"] = self._gate(rel, out["apply"].get("mutation_id"))
        return out

    def _gate(self, rel: str, mutation_id: Optional[str]) -> Dict[str, Any]:
        from brain.code_verify import verify_module_file

        report = verify_module_file(rel, repo_root=self.mut.root)
        if not report.get("ok"):
            # rollback
            rb = None
            if mutation_id:
                try:
                    rb = self.mut.rollback(mutation_id)
                except Exception as e:
                    rb = {"ok": False, "error": str(e)}
            else:
                # created new file — delete on red gate
                p = self.mut.root / rel
                if p.exists() and self.can_create(rel):
                    try:
                        p.unlink()
                        rb = {"ok": True, "deleted": rel}
                    except Exception as e:
                        rb = {"ok": False, "error": str(e)}
            report["rolled_back"] = rb
            report["kept"] = False
            logger.warning(f"CodeAuthor RED gate {rel}: {report.get('stage')}")
        else:
            report["kept"] = True
            report["rolled_back"] = None
            logger.info(f"CodeAuthor GREEN gate {rel}")
        write_json(self.dir / "last_verify.json", report)
        return report

    def _propose_create_write(self, rel: str, content: str, *, spec: str) -> Dict[str, Any]:
        try:
            ast.parse(content)
            compile(content, rel, "exec")
        except SyntaxError as e:
            return {"ok": False, "error": f"syntax: {e.msg}"}
        for pat in DANGEROUS_PATTERNS:
            if re.search(pat, content):
                return {"ok": False, "error": f"dangerous pattern: {pat}"}
        pid = "MU-" + str(uuid.uuid4())[:8]
        proposal = {
            "id": pid,
            "path": rel,
            "mode": "write",
            "strategy": "code_create",
            "reason": f"create {spec[:80]}",
            "author": "leon:code_author",
            "created_at": datetime.now().isoformat(),
            "syntax_ok": True,
            "quality": {"score": 70.0, "notes": ["new_module"], "reject": False},
            "status": "proposed",
            "_original": "",
            "_mutated": content,
            "create_prefix": True,
        }
        write_json(self.dir / "proposals" / f"{pid}.json", proposal)
        write_json(self.dir / "last_proposal.json", proposal)
        return {
            "ok": True,
            "proposal_id": pid,
            "path": rel,
            "status": "proposed",
            "enabled": self.mut.mutation_enabled(),
            "direct_write": True,
            "hint": None
            if self.mut.mutation_enabled()
            else "Apply: export LEON_ALLOW_MUTATE=1",
        }

    def _apply_create(self, rel: str, content: str, proposal_id: Optional[str]) -> Dict[str, Any]:
        if not self.mut.mutation_enabled():
            return {"ok": False, "error": "Set LEON_ALLOW_MUTATE=1"}
        if not self.can_create(rel):
            return {"ok": False, "error": "create not allowed"}
        target = (self.mut.root / rel).resolve()
        try:
            target.relative_to(self.mut.root.resolve())
        except ValueError:
            return {"ok": False, "error": "path escape"}
        target.parent.mkdir(parents=True, exist_ok=True)
        bak_dir = self.dir / "backups"
        bak_dir.mkdir(parents=True, exist_ok=True)
        mid = proposal_id or ("MU-" + uuid.uuid4().hex[:8])
        if target.exists():
            import shutil

            shutil.copy2(target, bak_dir / f"{mid}_{target.name}.bak")
        target.write_text(content, encoding="utf-8")
        return {
            "ok": True,
            "mutation_id": mid,
            "path": rel,
            "strategy": "code_create",
            "applied_at": datetime.now().isoformat(),
        }

    def write_code(
        self,
        goal: str,
        *,
        path: Optional[str] = None,
        create: bool = False,
        apply: bool = False,
        use_llm: bool = True,
        verify: bool = True,
    ) -> Dict[str, Any]:
        gen = self.generate_function(goal, use_llm=use_llm)
        if not gen.get("ok"):
            return {"ok": False, "stage": "generate", "detail": gen}

        if create:
            rel = path or self._default_new_path(goal, gen.get("name") or "helper")
            result = self.create_module(
                rel, code=gen["code"], spec=goal, apply=apply, verify=verify
            )
            return {
                "ok": self._overall_ok(result),
                "stage": "create",
                "generate": {"name": gen["name"], "source": gen["source"]},
                **result,
            }

        rel = path or self.mut.route_goal(goal).get("path")
        if not str(rel).endswith(".py"):
            rel = "brain/reasoning/engine.py"
        result = self.insert_into_module(
            str(rel), gen["code"], goal=goal, apply=apply, verify=verify
        )
        return {
            "ok": self._overall_ok(result),
            "stage": "insert",
            "generate": {"name": gen["name"], "source": gen["source"]},
            **result,
        }

    def _overall_ok(self, result: Dict[str, Any]) -> bool:
        if result.get("proposal") and not result["proposal"].get("ok"):
            return False
        if result.get("apply") is not None and not result["apply"].get("ok"):
            return False
        if result.get("verify") is not None and not result["verify"].get("kept", result["verify"].get("ok")):
            return False
        return True

    def _default_new_path(self, goal: str, name: str) -> str:
        g = goal.lower()
        if any(x in g for x in ("agent", "react", "tool")):
            return f"agents/leon_{name}.py"
        if any(x in g for x in ("vision", "image", "multimodal")):
            return f"multimodal/leon_{name}.py"
        if any(x in g for x in ("memory", "vector")):
            return f"memory/leon_{name}.py"
        if any(x in g for x in ("learn", "öyrən")):
            return f"learning/leon_{name}.py"
        return f"brain/reasoning/leon_{name}.py"

    def self_code_cycle(
        self,
        goal: str,
        *,
        apply: bool = False,
        create: bool = True,
        verify: bool = True,
    ) -> Dict[str, Any]:
        result = self.write_code(goal, create=create, apply=apply, use_llm=True, verify=verify)
        write_json(
            self.dir / "last_self_code.json",
            {
                "goal": goal,
                "at": datetime.now().isoformat(),
                "result_ok": result.get("ok"),
                "path": result.get("path"),
                "applied": bool(result.get("apply")),
                "kept": (result.get("verify") or {}).get("kept"),
            },
        )
        return result


code_author = CodeAuthor()


def write_own_code(
    goal: str, *, apply: bool = False, create: bool = True, verify: bool = True
) -> Dict[str, Any]:
    return CodeAuthor().self_code_cycle(goal, apply=apply, create=create, verify=verify)
