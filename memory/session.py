"""
Session Memory – multi-turn söhbət yaddaşı.

Mem0 / Letta üslubunda sadə sessiya konteksti.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import uuid


@dataclass
class Turn:
    role: str  # user | assistant | system
    content: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)


class SessionMemory:
    def __init__(self, session_id: Optional[str] = None, max_turns: int = 50):
        self.session_id = session_id or str(uuid.uuid4())[:12]
        self.max_turns = max_turns
        self.turns: List[Turn] = []
        self.metadata: Dict[str, Any] = {}

    def add(self, role: str, content: str, **meta) -> None:
        self.turns.append(Turn(role=role, content=content, metadata=meta))
        if len(self.turns) > self.max_turns:
            self.turns = self.turns[-self.max_turns :]

    def history(self, last_n: Optional[int] = None) -> List[Dict[str, str]]:
        items = self.turns if last_n is None else self.turns[-last_n:]
        return [{"role": t.role, "content": t.content} for t in items]

    def as_context(self, last_n: int = 10) -> str:
        lines = []
        for t in self.turns[-last_n:]:
            lines.append(f"{t.role.upper()}: {t.content[:300]}")
        return "\n".join(lines)

    def summary_prompt(self) -> str:
        return (
            "Aşağıdakı söhbəti 2-3 cümlə ilə xülasə et:\n"
            + self.as_context(20)
        )

    def clear(self) -> None:
        self.turns.clear()
