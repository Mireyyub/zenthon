"""Performance Evaluator – sistem performansını ölçür."""

from __future__ import annotations

from typing import Any, Dict, List
from datetime import datetime


class PerformanceEvaluator:
    def __init__(self):
        self._metrics: List[Dict[str, Any]] = []

    def record(
        self,
        name: str,
        value: float,
        unit: str = "",
        tags: Optional[Dict] = None,
    ) -> None:
        self._metrics.append({
            "name": name,
            "value": value,
            "unit": unit,
            "tags": tags or {},
            "timestamp": datetime.now().isoformat(),
        })

    def summary(self) -> Dict[str, Any]:
        if not self._metrics:
            return {"count": 0}
        by_name: Dict[str, List[float]] = {}
        for m in self._metrics:
            by_name.setdefault(m["name"], []).append(m["value"])
        return {
            name: {
                "count": len(vals),
                "avg": round(sum(vals) / len(vals), 4),
                "min": round(min(vals), 4),
                "max": round(max(vals), 4),
            }
            for name, vals in by_name.items()
        }

    def clear(self) -> None:
        self._metrics.clear()
