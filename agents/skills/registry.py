"""SkillRegistry — LEON-mega SkillRegistry ported to Python."""
from __future__ import annotations

from typing import Dict, List, Optional

from core.logger import logger
from agents.skills.base import Skill, SkillResult


class SkillRegistry:
    def __init__(self) -> None:
        self._skills: Dict[str, Skill] = {}

    def register(self, skill: Skill) -> None:
        self._skills[skill.name.lower()] = skill
        logger.info(f"[SkillRegistry] registered: {skill.name} (risk={skill.risk_tag})")

    def get(self, name: str) -> Optional[Skill]:
        return self._skills.get((name or "").lower())

    def list_skills(self) -> List[dict]:
        return [
            {"name": s.name, "description": s.description, "risk_tag": s.risk_tag}
            for s in sorted(self._skills.values(), key=lambda x: x.name.lower())
        ]

    def run(self, name: str, args: str = "", **kwargs) -> SkillResult:
        skill = self.get(name)
        if not skill:
            return SkillResult(success=False, error=f"Unknown skill: {name}")
        if skill.risk_tag not in ("none",):
            try:
                from security.gate import check_tool_allowed
                if not check_tool_allowed(skill.name):
                    return SkillResult(
                        success=False,
                        error=f"Skill blocked by security gate: {skill.name}",
                        risk_tag=skill.risk_tag,
                    )
            except Exception:
                pass
        try:
            return skill.run(args, **kwargs)
        except Exception as e:
            logger.error(f"[SkillRegistry] {name} failed: {e}")
            return SkillResult(success=False, error=str(e), risk_tag=skill.risk_tag)


_registry: Optional[SkillRegistry] = None


def get_skill_registry() -> SkillRegistry:
    global _registry
    if _registry is None:
        _registry = SkillRegistry()
        _register_builtins(_registry)
    return _registry


def _register_builtins(reg: SkillRegistry) -> None:
    from agents.skills.builtins import MathSkill, HelpSkill, ThinkSkill

    for cls in (MathSkill, HelpSkill, ThinkSkill):
        reg.register(cls())
