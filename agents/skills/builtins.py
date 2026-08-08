"""Builtin skills — LEON-mega + AgilBot domain ideas."""
from __future__ import annotations

import ast
import operator
from typing import Any

from agents.skills.base import Skill, SkillResult


class MathSkill(Skill):
    name = "math"
    description = "Təhlükəsiz riyazi ifadə hesabla (AgilBot/LEON-mega MathSkill)."
    risk_tag = "none"

    _ops = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Pow: operator.pow,
        ast.USub: operator.neg,
        ast.Mod: operator.mod,
    }

    def run(self, args: str = "", **kwargs: Any) -> SkillResult:
        expr = (args or kwargs.get("expression", "")).strip()
        if not expr:
            return SkillResult(success=False, error="expression boşdur")
        try:
            tree = ast.parse(expr, mode="eval")
            val = self._eval(tree.body)
            return SkillResult(success=True, output=val)
        except Exception as e:
            return SkillResult(success=False, error=str(e))

    def _eval(self, node):
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.BinOp):
            op = self._ops.get(type(node.op))
            if not op:
                raise ValueError("unsupported op")
            return op(self._eval(node.left), self._eval(node.right))
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
            return -self._eval(node.operand)
        raise ValueError("unsupported expression")


class HelpSkill(Skill):
    name = "help"
    description = "Mövcud skill-lərin siyahısı."
    risk_tag = "none"

    def run(self, args: str = "", **kwargs: Any) -> SkillResult:
        from agents.skills.registry import get_skill_registry

        skills = get_skill_registry().list_skills()
        lines = [f"- {s['name']}: {s['description']}" for s in skills]
        return SkillResult(success=True, output="\n".join(lines))


class ThinkSkill(Skill):
    name = "think"
    description = "Qısa daxili düşüncə / plan xülasəsi (LEON-mega ThinkSkill)."
    risk_tag = "none"

    def run(self, args: str = "", **kwargs: Any) -> SkillResult:
        text = (args or "").strip()
        if not text:
            return SkillResult(success=False, error="boş giriş")
        words = text.split()
        summary = " ".join(words[:40]) + ("..." if len(words) > 40 else "")
        return SkillResult(
            success=True,
            output={"thought": summary, "word_count": len(words)},
        )
