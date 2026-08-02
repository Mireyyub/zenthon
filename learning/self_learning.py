"""Self-Learning – feedback əsasında sadə özünü təkmilləşdirmə."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from core.logger import logger
from core.event_bus import event_bus
from learning.feedback import FeedbackCollector
from learning.evaluator import PerformanceEvaluator


class SelfLearning:
    def __init__(
        self,
        feedback: Optional[FeedbackCollector] = None,
        evaluator: Optional[PerformanceEvaluator] = None,
    ):
        self.feedback = feedback or FeedbackCollector()
        self.evaluator = evaluator or PerformanceEvaluator()
        self._lessons: List[str] = []

    def learn_from_feedback(self) -> List[str]:
        """Son feedback-lərdən dərs çıxar."""
        recent = self.feedback.recent(10)
        lessons = []
        for fb in recent:
            if fb["score"] < -0.3:
                lesson = f"Avoid pattern related to: {fb['content'][:80]}"
                lessons.append(lesson)
            elif fb["score"] > 0.5:
                lesson = f"Reinforce pattern: {fb['content'][:80]}"
                lessons.append(lesson)
        self._lessons.extend(lessons)
        if lessons:
            event_bus.publish("LearningFinished", {"lessons": len(lessons)}, source="learning")
            logger.info(f"SelfLearning: {len(lessons)} lessons extracted")
        return lessons

    def get_lessons(self) -> List[str]:
        return list(self._lessons)

    def suggest_improvement(self) -> Dict[str, Any]:
        avg = self.feedback.average_score()
        metrics = self.evaluator.summary()
        return {
            "avg_feedback": round(avg, 3),
            "metrics": metrics,
            "lessons_count": len(self._lessons),
            "recommendation": (
                "Sistem stabil görünür" if avg >= 0.2
                else "Daha çox müsbət nümunə və feedback lazımdır"
            ),
        }
