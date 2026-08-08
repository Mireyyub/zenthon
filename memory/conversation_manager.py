"""
Conversation Manager — from Drive zenthon_v08.
Session multi-turn with optional disk persistence under data/leon/conversations.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.logger import logger
from core.persistence import write_json, read_json


@dataclass
class Message:
    role: str
    content: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)
    msg_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])

    def to_dict(self) -> Dict[str, Any]:
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
            "msg_id": self.msg_id,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Message":
        return cls(
            role=d.get("role", "user"),
            content=d.get("content", ""),
            timestamp=d.get("timestamp") or datetime.now().isoformat(),
            metadata=d.get("metadata") or {},
            msg_id=d.get("msg_id") or str(uuid.uuid4())[:8],
        )


class ConversationManager:
    def __init__(self, session_id: Optional[str] = None, max_messages: int = 40):
        self.session_id = session_id or str(uuid.uuid4())[:10]
        self.max_messages = max_messages
        self.messages: List[Message] = []
        try:
            from core.config import config

            self.dir = Path(config.path.leon_dir) / "conversations"
        except Exception:
            self.dir = Path("data/leon/conversations")
        self.dir.mkdir(parents=True, exist_ok=True)

    def add(self, role: str, content: str, **meta) -> Message:
        msg = Message(role=role, content=content, metadata=meta)
        self.messages.append(msg)
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages :]
        return msg

    def as_context(self, last_n: int = 8) -> str:
        parts = []
        for m in self.messages[-last_n:]:
            parts.append(f"{m.role}: {m.content[:500]}")
        return "\n".join(parts)

    def save(self) -> Path:
        path = self.dir / f"{self.session_id}.json"
        write_json(
            path,
            {
                "session_id": self.session_id,
                "messages": [m.to_dict() for m in self.messages],
                "updated_at": datetime.now().isoformat(),
            },
        )
        return path

    def load(self, session_id: Optional[str] = None) -> bool:
        sid = session_id or self.session_id
        data = read_json(self.dir / f"{sid}.json", default=None)
        if not data:
            return False
        self.session_id = data.get("session_id", sid)
        self.messages = [Message.from_dict(m) for m in (data.get("messages") or [])]
        logger.info(f"Conversation loaded {self.session_id} n={len(self.messages)}")
        return True

    def clear(self) -> None:
        self.messages.clear()
