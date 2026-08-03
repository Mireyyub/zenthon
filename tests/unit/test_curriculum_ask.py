"""Curriculum ask fuzzy matching."""

from __future__ import annotations


def test_similarity_and_ask_patterns():
    from curriculum.engine import _similarity, CurriculumEngine

    assert _similarity("Daş mövcuddurmu?", "Daş mövcuddurmu?") >= 0.99
    assert _similarity("Daş mövcuddurmu", "Daş mövcuddurmu?") >= 0.9

    eng = CurriculumEngine()
    # even before teach, pattern classify path
    r = eng.ask("kvadrat dairə mövcuddurmu?")
    assert r.get("matched") is True
    assert "xeyr" in str(r.get("answer")).lower()
