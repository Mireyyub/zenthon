"""
Sandbox filesystem tools.
Yalnız data/leon/sandbox və data/leon altında oxu/yaz.
run_python: restricted exec + optional subprocess isolation.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List
import ast
import operator as op


def _roots() -> List[Path]:
    try:
        from core.config import config

        leon = Path(config.path.leon_dir)
    except Exception:
        leon = Path("data/leon")
    sandbox = leon / "sandbox"
    sandbox.mkdir(parents=True, exist_ok=True)
    return [sandbox.resolve(), leon.resolve()]


def _resolve_safe(path: str) -> Path:
    roots = _roots()
    p = Path(path).expanduser()
    if not p.is_absolute():
        p = roots[0] / p
    p = p.resolve()
    for root in roots:
        try:
            p.relative_to(root)
            return p
        except ValueError:
            continue
    raise PermissionError(f"Path outside sandbox: {path}")


def list_dir(path: str = ".") -> Dict[str, Any]:
    p = _resolve_safe(path)
    if not p.exists():
        return {"error": f"not found: {path}", "entries": []}
    if not p.is_dir():
        return {"error": "not a directory", "entries": []}
    entries = sorted([c.name + ("/" if c.is_dir() else "") for c in p.iterdir()])
    return {"path": str(p), "entries": entries[:200]}


def read_file(path: str, max_bytes: int = 50_000) -> Dict[str, Any]:
    p = _resolve_safe(path)
    if not p.exists() or not p.is_file():
        return {"error": f"file not found: {path}"}
    data = p.read_bytes()[:max_bytes]
    try:
        text = data.decode("utf-8")
    except Exception:
        text = data.decode("utf-8", errors="replace")
    return {"path": str(p), "content": text, "bytes": len(data)}


def write_file(path: str, content: str = "") -> Dict[str, Any]:
    p = _resolve_safe(path)
    sandbox = _roots()[0]
    try:
        p.relative_to(sandbox)
    except ValueError:
        raise PermissionError("write yalnız sandbox/ içində icazəlidir")
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content or "", encoding="utf-8")
    return {"path": str(p), "written": len(content or "")}


_ALLOWED_OPS = {
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv,
    ast.Pow: op.pow,
    ast.USub: op.neg,
    ast.Mod: op.mod,
}


def _eval_ast(node):
    if isinstance(node, ast.Expression):
        return _eval_ast(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _ALLOWED_OPS:
        return _ALLOWED_OPS[type(node.op)](_eval_ast(node.left), _eval_ast(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _ALLOWED_OPS:
        return _ALLOWED_OPS[type(node.op)](_eval_ast(node.operand))
    raise ValueError("unsupported expression")


def calc(expression: str = "") -> Dict[str, Any]:
    try:
        tree = ast.parse(expression, mode="eval")
        val = _eval_ast(tree)
        return {"expression": expression, "result": val}
    except Exception as e:
        return {"expression": expression, "error": str(e)}


def run_python(code: str = "", timeout: float = 2.0) -> Dict[str, Any]:
    """
    Prefer security.Sandbox subprocess isolation; fall back to restricted exec.
    """
    try:
        from security.sandbox import Sandbox

        return Sandbox(timeout_seconds=max(1, int(timeout))).run_python(code)
    except Exception as e:
        # fall back if import/signal issues
        pass

    forbidden = (
        "import", "open", "exec", "eval", "__", "os.", "sys.", "subprocess",
        "socket", "pathlib", "shutil", "compile",
    )
    low = code.lower()
    for f in forbidden:
        if f in low:
            return {"error": f"forbidden token: {f}"}

    safe_builtins = {
        "abs": abs,
        "min": min,
        "max": max,
        "sum": sum,
        "len": len,
        "range": range,
        "str": str,
        "int": int,
        "float": float,
        "bool": bool,
        "list": list,
        "dict": dict,
        "print": print,
    }
    local: Dict[str, Any] = {}
    try:
        compile(code, "<sandbox>", "exec")
        exec(code, {"__builtins__": safe_builtins}, local)  # noqa: S102
        out = {k: repr(v)[:200] for k, v in local.items() if not k.startswith("_")}
        return {"ok": True, "locals": out, "mode": "restricted_exec"}
    except Exception as e:
        return {"ok": False, "error": str(e)}
