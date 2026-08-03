"""
LEON Genesis Curriculum.

    from curriculum import CurriculumEngine

    eng = CurriculumEngine()
    eng.teach_volume("01")
"""

from curriculum.engine import CurriculumEngine, Lesson
from curriculum.loader import load_lesson, list_lessons
from curriculum.volume import list_volumes, load_volume, load_train_jsonl, load_eval_jsonl

__all__ = [
    "CurriculumEngine",
    "Lesson",
    "load_lesson",
    "list_lessons",
    "list_volumes",
    "load_volume",
    "load_train_jsonl",
    "load_eval_jsonl",
]
