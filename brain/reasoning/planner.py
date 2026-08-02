"""Planner"""

from typing import List

from core.logger import logger


class Planner:
    def create_plan(self, goal: str, max_steps: int = 6) -> List[str]:
        logger.info(f"Creating plan for goal: {goal}")
        plan = [
            f"1. Məqsədi analiz et: {goal[:80]}",
            "2. Lazımi məlumatları və resursları müəyyənləşdir",
            "3. Alternativ yolları qiymətləndir",
            "4. Ən uyğun yolu seç və alt-tapşırıqlara böl",
            "5. Hər alt-tapşırığı icra et və nəticəni yoxla",
            "6. Ümumi nəticəni qiymətləndir və lazım gələrsə planı yenilə",
        ]
        return plan[:max_steps]

    def refine_plan(self, current_plan: List[str], feedback: str) -> List[str]:
        refined = current_plan.copy()
        refined.append(f"Yenilənmə (feedback): {feedback[:100]}")
        return refined
