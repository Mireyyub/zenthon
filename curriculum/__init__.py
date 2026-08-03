"""
LEON Genesis Curriculum.

    from curriculum import CurriculumEngine

    eng = CurriculumEngine()
    eng.teach_volume("01")          # Foundation tam cild
    eng.teach("000001")             # tək dərs
"""

from curriculum.engine import CurriculumEngine, Lesson
from curriculum.loader import load_lesson, list_lessons
from curriculum.volume import list_volumes, load_volume

__all__ = [
    "CurriculumEngine",
    "Lesson",
    "load_lesson",
    "list_lessons",
    "list_volumes",
    "load_volume",
]
