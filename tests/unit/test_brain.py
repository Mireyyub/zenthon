"""Unit tests for ThinkingBrain and evaluation metrics."""

from evaluation.metrics import EvaluationMetrics


def test_keyword_coverage():
    s = EvaluationMetrics.keyword_coverage("süni intellekt öyrənir", ["intellekt", "öyrən"])
    assert s == 1.0


def test_composite_score():
    scores = EvaluationMetrics.composite(
        "Bu kifayət qədər uzun bir cavabdır və intellekt sözü var",
        confidence=0.8,
        expected_keywords=["intellekt"],
    )
    assert "composite" in scores
    assert 0 <= scores["composite"] <= 1


def test_thinking_brain_basic():
    from brain import ThinkingBrain

    brain = ThinkingBrain(name="TestBrain", enable_meta=True)
    result = brain.think("2+2 neçədir?", reasoning_mode="cot", allow_rethink=False)
    assert "conclusion" in result
    assert "confidence" in result
    assert result["cycle"] >= 1


def test_brain_state():
    from brain import ThinkingBrain

    brain = ThinkingBrain(name="StateTest")
    brain.think("salam", allow_rethink=False)
    st = brain.get_state()
    assert st["cycle_count"] >= 1
    assert "working_memory_size" in st
