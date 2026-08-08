"""
Transfer evaluation — measure knowledge carry-over across volumes.

Protocol:
  1) Optional teach source volumes only
  2) Eval target volume WITHOUT teaching target (zero-shot transfer)
  3) Optional teach target and re-eval (upper bound)
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.persistence import write_json
from core.logger import logger


def _dir() -> Path:
    try:
        from core.config import config

        d = Path(config.path.leon_dir) / "eval"
    except Exception:
        d = Path("data/leon/eval")
    d.mkdir(parents=True, exist_ok=True)
    return d


def transfer_eval(
    source_volumes: Optional[List[str]] = None,
    target_volume: str = "03",
    *,
    teach_source: bool = True,
    teach_target_after: bool = True,
) -> Dict[str, Any]:
    from curriculum import CurriculumEngine

    sources = source_volumes or ["01", "02"]
    eng = CurriculumEngine()
    report: Dict[str, Any] = {
        "at": datetime.now().isoformat(),
        "sources": sources,
        "target": target_volume,
        "teach_source": teach_source,
        "phases": {},
    }

    if teach_source:
        taught = {}
        for vid in sources:
            try:
                taught[vid] = eng.teach_volume(vid)
            except Exception as e:
                taught[vid] = {"error": str(e)}
        report["phases"]["teach_source"] = {
            vid: {
                "lessons_passed": (taught[vid] or {}).get("lessons_passed"),
                "error": (taught[vid] or {}).get("error"),
            }
            for vid in taught
        }

    # zero-shot on target
    try:
        zero = eng.run_eval(target_volume)
    except Exception as e:
        zero = {"error": str(e), "pass_rate": 0.0, "passed": 0, "total": 0}
    report["phases"]["zero_shot_target"] = {
        "pass_rate": zero.get("pass_rate"),
        "passed": zero.get("passed"),
        "total": zero.get("total"),
        "error": zero.get("error"),
    }

    upper = None
    if teach_target_after:
        try:
            eng.teach_volume(target_volume)
            upper = eng.run_eval(target_volume)
        except Exception as e:
            upper = {"error": str(e), "pass_rate": 0.0}
        report["phases"]["after_teach_target"] = {
            "pass_rate": upper.get("pass_rate"),
            "passed": upper.get("passed"),
            "total": upper.get("total"),
            "error": upper.get("error"),
        }

    z = float(zero.get("pass_rate") or 0)
    u = float((upper or {}).get("pass_rate") or 0) if upper else None
    report["transfer_gap"] = None if u is None else round(u - z, 4)
    report["zero_shot_pass_rate"] = z
    report["upper_pass_rate"] = u
    report["interpretation"] = (
        "zero_shot high → strong transfer; large gap → target needs direct teaching"
    )

    write_json(_dir() / "last_transfer.json", report)
    logger.info(
        f"Transfer {sources}→{target_volume}: zero={z} upper={u} gap={report['transfer_gap']}"
    )
    return report


def multi_transfer(
    pairs: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    pairs = pairs or [
        {"sources": ["01"], "target": "03"},
        {"sources": ["01", "02"], "target": "03"},
        {"sources": ["01"], "target": "04"},
        {"sources": ["01", "05"], "target": "06"},
    ]
    rows = []
    for p in pairs:
        rows.append(
            transfer_eval(
                source_volumes=p.get("sources"),
                target_volume=str(p.get("target")),
                teach_source=True,
                teach_target_after=True,
            )
        )
    out = {"at": datetime.now().isoformat(), "runs": rows}
    write_json(_dir() / "last_multi_transfer.json", out)
    return out
