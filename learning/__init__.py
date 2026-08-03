"""Leon Learning Engine + Curriculum bridge."""

from learning.feedback import FeedbackCollector
from learning.evaluator import PerformanceEvaluator
from learning.self_learning import SelfLearning
from learning.engine import LearningEngine, learning_engine

__all__ = [
    "FeedbackCollector",
    "PerformanceEvaluator",
    "SelfLearning",
    "LearningEngine",
    "learning_engine",
    "teach_lesson",
    "bootstrap_from_specs",
]


def teach_lesson(lesson_id: str = "000001"):
    from curriculum import CurriculumEngine
    return CurriculumEngine().teach(lesson_id)


def bootstrap_from_specs(volume_id: str = "01") -> Dict:
    """
    Spesifikasiya + curriculum + genome birləşməsi:
    1) Genome faktlara
    2) Curriculum volume teach
    3) train.jsonl → LearningEngine
    """
    report = {}
    try:
        from genome.loader import activate_genes_into_facts, list_genes
        report["genes"] = list_genes()
        report["genes_activated"] = activate_genes_into_facts()
    except Exception as e:
        report["genes_error"] = str(e)

    try:
        from curriculum import CurriculumEngine
        eng = CurriculumEngine()
        report["volume"] = eng.teach_volume(volume_id)
    except Exception as e:
        report["volume_error"] = str(e)

    try:
        report["learning"] = learning_engine.from_curriculum(volume_id)
        report["learning_stats"] = learning_engine.stats()
    except Exception as e:
        report["learning_error"] = str(e)

    return report
