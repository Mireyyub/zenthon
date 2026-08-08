"""CLI for Leon self-view (body awareness)."""

from __future__ import annotations

import json
from typing import Any


def run_self(args: Any) -> None:
    from brain.self_view import SelfView

    v = SelfView()
    cmd = getattr(args, "self_cmd", None) or "body"

    if cmd == "body" or cmd == "status":
        print(json.dumps(v.body(), ensure_ascii=False, indent=2, default=str))
        return
    if cmd == "map":
        print(json.dumps(v.map(), ensure_ascii=False, indent=2, default=str))
        return
    if cmd == "cell":
        name = getattr(args, "name", None) or "brain"
        print(json.dumps(v.cell(name), ensure_ascii=False, indent=2, default=str))
        return
    if cmd == "read":
        path = getattr(args, "path", None)
        if not path:
            print(json.dumps({"ok": False, "error": "--path required"}))
            return
        print(
            json.dumps(
                v.read(
                    path,
                    start=int(getattr(args, "start", 1) or 1),
                    end=getattr(args, "end", None),
                    max_lines=int(getattr(args, "max_lines", 200) or 200),
                ),
                ensure_ascii=False,
                indent=2,
                default=str,
            )
        )
        return
    if cmd == "symbols":
        path = getattr(args, "path", None)
        if not path:
            print(json.dumps({"ok": False, "error": "--path required"}))
            return
        print(json.dumps(v.symbols(path), ensure_ascii=False, indent=2, default=str))
        return
    if cmd == "search":
        q = getattr(args, "query", None) or ""
        print(
            json.dumps(
                v.search(q, path_prefix=getattr(args, "prefix", "") or ""),
                ensure_ascii=False,
                indent=2,
                default=str,
            )
        )
        return
    if cmd == "mutable":
        path = getattr(args, "path", None) or ""
        print(json.dumps(v.mutability(path), ensure_ascii=False, indent=2))
        return

    print("self body|map|cell|read|symbols|search|mutable")
