"""Evaluation metrics for brain / agent outputs."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import re


class EvaluationMetrics:
    """Sadə, asılılıqsız metriklər."""

    @staticmethod
    def keyword_coverage(output: str, expected_keywords: List[str]) -> float:
        if not expected_keywords:
            return 1.0
        out = (output or "").lower()
        hit = sum(1 for k in expected_keywords if k.lower() in out)
        return round(hit / len(expected_keywords), 3)

    @staticmethod
    def length_score(output: str, min_len: int = 20, max_len: int = 2000) -> float:
        n = len(output or "")
        if n < min_len:
            return round(n / min_len, 3)
        if n > max_len:
            return round(max(0.0, 1.0 - (n - max_len) / max_len), 3)
        return 1.0

    @staticmethod
    def confidence_score(confidence: float) -> float:
        return round(max(0.0, min(1.0, float(confidence))), 3)

    @staticmethod
    def composite(
        output: str,
        confidence: float = 0.5,
        expected_keywords: Optional[List[str]] = None,
        weights: Optional[Dict[str, float]] = None,
    ) -> Dict[str, float]:
        w = weights or {"keywords": 0.4, "length": 0.2, "confidence": 0.4}
        kw = EvaluationMetrics.keyword_coverage(output, expected_keywords or [])
        ln = EvaluationMetrics.length_score(output)
        cf = EvaluationMetrics.confidence_score(confidence)
        total = w["keywords"] * kw + w["length"] * ln + w["confidence"] * cf
        return {
            "keyword_coverage": kw,
            "length_score": ln,
            "confidence_score": cf,
            "composite": round(total, 3),
        }
