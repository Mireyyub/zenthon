"""
Gücləndirilmiş Episodic Memory.

Hadisələri importance və confidence ilə saxlayır.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid


class EpisodicMemory:
    def __init__(self, max_episodes: int = 800):
        self.max_episodes = max_episodes
        self._episodes: List[Dict[str, Any]] = []

    def store_episode(
        self,
        event: str,
        reasoning_trace: Optional[List[str]] = None,
        outcome: Optional[str] = None,
        metadata: Optional[Dict] = None,
    ) -> str:
        episode_id = str(uuid.uuid4())[:10]
        meta = metadata or {}
        importance = float(meta.get("importance", 0.5))
        confidence = float(meta.get("confidence", 0.5))

        episode = {
            "id": episode_id,
            "event": event,
            "reasoning_trace": reasoning_trace or [],
            "outcome": outcome,
            "metadata": meta,
            "importance": importance,
            "confidence": confidence,
            "timestamp": datetime.now().isoformat(),
            "access_count": 0,
        }
        self._episodes.append(episode)

        if len(self._episodes) > self.max_episodes:
            # Ən az vacib olanı sil
            self._episodes.sort(key=lambda e: e["importance"] * 0.7 + e["confidence"] * 0.3)
            self._episodes.pop(0)

        return episode_id

    def retrieve(self, query: str, top_k: int = 3) -> List[str]:
        query_lower = query.lower()
        scored = []

        for ep in self._episodes:
            text = f"{ep['event']} {ep.get('outcome', '')}".lower()
            keyword_score = sum(1 for word in query_lower.split() if word in text)
            if keyword_score == 0:
                continue
            score = (
                keyword_score * 1.0
                + ep["importance"] * 0.6
                + ep["confidence"] * 0.3
            )
            scored.append((score, ep))

        scored.sort(key=lambda x: x[0], reverse=True)

        results = []
        for score, ep in scored[:top_k]:
            ep["access_count"] += 1
            results.append(f"[Episode] {ep['event'][:130]}")

        return results

    def get_recent(self, n: int = 5) -> List[Dict[str, Any]]:
        return self._episodes[-n:]

    def get_high_importance(self, threshold: float = 0.7, limit: int = 10) -> List[Dict]:
        high = [e for e in self._episodes if e["importance"] >= threshold]
        high.sort(key=lambda e: e["importance"], reverse=True)
        return high[:limit]

    def clear(self) -> None:
        self._episodes.clear()
