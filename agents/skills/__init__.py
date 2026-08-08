"""Skill system ported from LEON-mega (C#) to Python for zenthon."""
from agents.skills.base import Skill, SkillResult
from agents.skills.registry import SkillRegistry, get_skill_registry

__all__ = ["Skill", "SkillResult", "SkillRegistry", "get_skill_registry"]
