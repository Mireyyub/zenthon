"""CLI for CognitiveCycle."""

from __future__ import annotations

import json
from typing import Any


def run_cycle(args: Any) -> None:
    from brain.cognitive_cycle import CognitiveCycle

    q = getattr(args, "query", None) or getattr(args, "q", None)
    if not q:
        print(json.dumps({"ok": False, "error": "query required"}))
        return
    out = CognitiveCycle().run(
        q,
        goal=getattr(args, "goal", None),
        image_path=getattr(args, "image", None),
        audio_path=getattr(args, "audio", None),
        agent_type=getattr(args, "agent", None),
        allow_experimental_agent=bool(getattr(args, "experimental", False)),
        learn=not bool(getattr(args, "no_learn", False)),
        reflect=not bool(getattr(args, "no_reflect", False)),
    )
    if getattr(args, "json", False):
        print(json.dumps(out, ensure_ascii=False, indent=2, default=str))
        return
    print(f"Answer     : {out.get('answer')}")
    print(f"Confidence : {out.get('confidence')}")
    print(f"Source     : {out.get('source')}")
    print(f"Cycle      : {out.get('cycle_id')}")
    print(f"Modalities : {(out.get('perception') or {}).get('modalities')}")
    ref = out.get("reflection") or {}
    if ref:
        print(f"Reflect    : {ref.get('quality')} issues={ref.get('issues')}")
    if out.get("action"):
        print(f"Act        : {out['action']}")
    print(f"Phases     : {[p.get('phase') for p in (out.get('phases') or [])]}")
