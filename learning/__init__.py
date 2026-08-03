"""Leon Learning Engine + Curriculum bridge."""

from learning.feedback import FeedbackCollector
from learning.evaluator import PerformanceEvaluator
from learning.self_learning import SelfLearning

__all__ = ["FeedbackCollector", "PerformanceEvaluator", "SelfLearning"]


def teach_lesson(lesson_id: str = "000001"):
    """Qısa yol: curriculum dərsini öyrət."""
    from curriculum import CurriculumEngine

    return CurriculumEngine().teach(lesson_id)
