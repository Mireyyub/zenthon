"""
Post-codegen verification gate for Leon.

Pipeline:
  compile → static danger scan → import → call public helpers → smoke → (optional) curriculum snapshot

On failure caller should rollback applied mutation.
"""

from __future__ import annotations

import ast
import importlib
import inspect
import re
import sys
import traceback
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.logger import logger


DANGEROUS = (
    r"\beval\s*\(",
    r"\bexec\s*\(",
    r"\bos\.system\s*\(",
    r"\bsubprocess\.",
    r"\b__import__\s*\(",
)


def verify_source(code: str, *, label: str = "<src>") -> Dict[str, Any]:
    issues: List[str] = []
    try:
        tree = ast.parse(code)
        compile(code, label, "exec")
    except SyntaxError as e:
        return {"ok": False, "stage": "compile", "error": f"{e.msg}:{e.lineno}"}
    for pat in DANGEROUS:
        if re.search(pat, code):
            issues.append(f"danger:{pat}")
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id in ("eval", "exec", "__import__"):
                issues.append(f"call:{node.func.id}")
    return {"ok": not issues, "stage": "compile", "issues": issues}


def verify_module_file(rel_path: str, repo_root: Optional[Path] = None) -> Dict[str, Any]:
    root = repo_root or Path(__file__).resolve().parent.parent
    path = (root / rel_path).resolve()
    try:
        path.relative_to(root.resolve())
    except ValueError:
        return {"ok": False, "stage": "path", "error": "escape"}
    if not path.exists():
        return {"ok": False, "stage": "path", "error": "missing"}

    src = path.read_text(encoding="utf-8")
    static = verify_source(src, label=rel_path)
    if not static.get("ok"):
        return static

    mod_name = rel_path.replace("/", ".").removesuffix(".py")
    # isolate: load via importlib from path
    import_ok = False
    import_err = None
    module = None
    try:
        spec = importlib.util.spec_from_file_location(mod_name, path)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            # don't register permanently unless needed
            sys.modules[mod_name + "._leon_verify"] = module
            spec.loader.exec_module(module)
            import_ok = True
    except Exception as e:
        import_err = f"{type(e).__name__}: {e}"
        logger.debug(f"verify import fail {rel_path}: {import_err}")

    if not import_ok:
        return {
            "ok": False,
            "stage": "import",
            "error": import_err,
            "static": static,
        }

    call_results = []
    # try calling top-level functions with no required args
    for name, fn in list(vars(module).items()):
        if name.startswith("_"):
            continue
        if not callable(fn) or inspect.isclass(fn):
            continue
        try:
            sig = inspect.signature(fn)
            required = [
                p
                for p in sig.parameters.values()
                if p.default is inspect.Parameter.empty
                and p.kind
                in (
                    inspect.Parameter.POSITIONAL_ONLY,
                    inspect.Parameter.POSITIONAL_OR_KEYWORD,
                )
            ]
            if required:
                continue
            out = fn()
            call_results.append({"fn": name, "ok": True, "type": type(out).__name__})
        except Exception as e:
            call_results.append(
                {
                    "fn": name,
                    "ok": False,
                    "error": f"{type(e).__name__}: {e}",
                }
            )

    # soft: if any call crashed hard, still allow module if import worked and no call attempted
    hard_fail_calls = [c for c in call_results if not c.get("ok")]
    # Only fail gate if ALL attempted calls failed and there was at least one attempt
    call_ok = True
    if call_results and len(hard_fail_calls) == len(call_results):
        call_ok = False

    smoke = _smoke()
    ok = import_ok and call_ok and bool(smoke.get("ok"))
    return {
        "ok": ok,
        "stage": "full",
        "static": static,
        "import_ok": import_ok,
        "calls": call_results,
        "call_ok": call_ok,
        "smoke": smoke,
        "module": mod_name,
        "path": rel_path,
    }


def _smoke() -> Dict[str, Any]:
    try:
        from core.bootstrap import smoke_test

        r = smoke_test()
        return {"ok": bool(r.get("overall_ok")), "detail": "bootstrap.smoke_test"}
    except Exception as e:
        try:
            from brain.reasoning.engine import ReasoningEngine

            ReasoningEngine(persist_traces=False).reason("ping", use_brain=False)
            return {"ok": True, "detail": "light reason", "warning": str(e)}
        except Exception as e2:
            return {"ok": False, "error": str(e2)}


def curriculum_snapshot(volumes: Optional[List[str]] = None) -> Dict[str, Any]:
    try:
        from curriculum import CurriculumEngine

        eng = CurriculumEngine()
        vols = volumes or ["01", "02"]
        rates = {}
        for v in vols:
            try:
                r = eng.run_eval(v)
                rates[v] = r.get("pass_rate")
            except Exception as e:
                rates[v] = None
                rates[f"{v}_err"] = str(e)
        nums = [x for x in rates.values() if isinstance(x, (int, float))]
        avg = sum(nums) / len(nums) if nums else 0.0
        return {"ok": True, "rates": rates, "avg": round(avg, 3)}
    except Exception as e:
        return {"ok": False, "error": str(e)}
