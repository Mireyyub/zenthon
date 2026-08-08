"""Skill protocol — LEON-mega ISkill rewritten for Python/zenthon."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class SkillResult:
    success: bool
    output: Any = None
    error: Optional[str] = None
    risk_tag: str = "none"

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "output": self.output,
            "error": self.error,
            "risk_tag": self.risk_tag,
        }


class Skill(ABC):
    """One capability (tool) Leon can invoke."""

    name: str = "skill"
    description: str = ""
    risk_tag: str = "none"  # none | shell | network | file_write | file_delete

    @abstractmethod
    def run(self, args: str = "", **kwargs: Any) -> SkillResult:
        ...
