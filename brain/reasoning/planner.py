"""
Gücləndirilmiş Planner.

Məqsəddən hierarchical plan yaradır və geribildirimə görə yeniləyir.
"""

from typing import List, Optional, Dict, Any

from core.logger import logger


class Planner:
    def create_plan(self, goal: str, max_steps: int = 7) -> List[str]:
        logger.info(f"Creating plan for goal: {goal}")

        goal_lower = goal.lower()

        # Məqsəd növünə görə şablon seç
        if any(k in goal_lower for k in ("qur", "build", "yarat", "implement", "inkişaf")):
            template = [
                f"1. Məqsədi və uğur meyarlarını dəqiqləşdir: {goal[:70]}",
                "2. Lazımi komponentləri və asılılıqları siyahıla",
                "3. Minimal işlək versiyanı (MVP) təyin et",
                "4. Komponentləri prioritet sırası ilə reallaşdır",
                "5. Hər mərhələdə test və validasiya et",
                "6. İnteqrasiya et və bütün sistemi yoxla",
                "7. Sənədləşdir və növbəti iterasiyaya hazırlaş",
            ]
        elif any(k in goal_lower for k in ("analiz", "tədqiq", "araşdır", "öyrən")):
            template = [
                f"1. Tədqiqat sualını dəqiqləşdir: {goal[:70]}",
                "2. Mövcud bilik və mənbələri topla",
                "3. Hipotezlər irəli sür",
                "4. Məlumatları topla və analiz et",
                "5. Nəticələri qiymətləndir və sintez et",
                "6. Nəticə və tövsiyələri formalaşdır",
            ]
        else:
            template = [
                f"1. Məqsədi analiz et: {goal[:80]}",
                "2. Lazımi məlumatları və resursları müəyyənləşdir",
                "3. Alternativ yolları qiymətləndir",
                "4. Ən uyğun yolu seç və alt-tapşırıqlara böl",
                "5. Hər alt-tapşırığı icra et və nəticəni yoxla",
                "6. Ümumi nəticəni qiymətləndir",
                "7. Lazım gələrsə planı yenilə və təkrar et",
            ]

        return template[:max_steps]

    def refine_plan(
        self,
        current_plan: List[str],
        feedback: str,
        success: Optional[bool] = None,
    ) -> List[str]:
        refined = current_plan.copy()
        status = "uğurlu" if success else ("uğursuz" if success is False else "qeyri-müəyyən")
        refined.append(
            f"Yenilənmə [{status}]: {feedback[:120]}"
        )
        if success is False:
            refined.append("Korreksiya: Alternativ yanaşma və ya əlavə addım əlavə et.")
        return refined

    def evaluate_progress(
        self, plan: List[str], completed_steps: int
    ) -> Dict[str, Any]:
        total = len(plan)
        ratio = completed_steps / total if total else 0.0
        return {
            "total_steps": total,
            "completed": completed_steps,
            "progress": round(ratio, 3),
            "remaining": max(0, total - completed_steps),
            "status": "done" if ratio >= 1.0 else ("on_track" if ratio >= 0.4 else "early"),
        }
