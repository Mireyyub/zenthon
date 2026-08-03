"""
LEON Curriculum – təlim sistemi.

    from curriculum import CurriculumEngine

    eng = CurriculumEngine()
    eng.teach("000001")  # Existence
"""

from curriculum.engine import CurriculumEngine, Lesson
from curriculum.loader import load_lesson, list_lessons

__all__ = ["CurriculumEngine", "Lesson", "load_lesson", "list_lessons"]
