"""Episodic Memory"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid


class EpisodicMemory:
    def __init__(self, max_episodes: int = 500):
        self.max_episodes = max_episodes
        self._episodes: List[Dict[str, Any]] = []

    def store_episode(self, event: str, reasoning_trace: Optional[List[str]] = None,
                      outcome: Optional[str] = None, metadata: Optional[Dict] = None) -> str:
        episode_id = str(uuid.uuid4())[:10]
        self._episodes.append({
            "id": episode_id, "event": event,
            "reasoning_trace": reasoning_trace or [], "outcome": outcome,
            "metadata": metadata or {}, "timestamp": datetime.now().isoformat(),
        })
        if len(self._episodes) > self.max_episodes:
            self._episodes.pop(0)
        return episode_id

    def retrieve(self, query: str, top_k: int = 3) -> List[str]:
        query_lower = query.lower()
        scored = []
        for ep in self._episodes:
            score = sum(1 for word in query_lower.split() if word in f"{ep['event']} {ep.get('outcome', '')}".lower())
            if score > 0:
                scored.append((score, f"[Episode] {ep['event'][:120]}"))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [val for _, val in scored[:top_k]]

    def clear(self) -> None:
        self._episodes.clear()
