"""Memory Manager – bütün yaddaş növlərini birləşdirir."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from core.logger import logger
from core.event_bus import event_bus
from memory.working_memory import WorkingMemory
from memory.semantic import SemanticMemory
from memory.vector_memory import VectorMemory

# Brain memory-ləri də istifadə et
try:
    from brain.memory.short_term import ShortTermMemory
    from brain.memory.long_term import LongTermMemory
    from brain.memory.episodic import EpisodicMemory
except ImportError:
    ShortTermMemory = LongTermMemory = EpisodicMemory = None


class MemoryManager:
    """Vahid yaddaş interfeysi."""

    def __init__(self):
        self.working = WorkingMemory()
        self.semantic = SemanticMemory()
        self.vector = VectorMemory()
        self.short_term = ShortTermMemory() if ShortTermMemory else None
        self.long_term = LongTermMemory() if LongTermMemory else None
        self.episodic = EpisodicMemory() if EpisodicMemory else None
        logger.info("MemoryManager initialized.")

    def remember(self, text: str, kind: str = "vector", **kwargs) -> str:
        """Ümumi yadda saxlama."""
        if kind == "semantic":
            return self.semantic.store_fact(
                kwargs.get("subject", text),
                kwargs.get("predicate", "is"),
                kwargs.get("object", "known"),
                kwargs.get("confidence", 1.0),
            )
        if kind == "working":
            return self.working.add(text, tag=kwargs.get("tag", "general"))
        if kind == "long_term" and self.long_term:
            return self.long_term.store(kwargs.get("key", text[:40]), text)
        # default: vector
        doc_id = self.vector.add(text, metadata=kwargs.get("metadata"))
        event_bus.publish("MemoryUpdated", {"kind": kind, "id": doc_id}, source="memory")
        return doc_id

    def recall(self, query: str, top_k: int = 5) -> Dict[str, List]:
        """Bütün yaddaşlardan axtar."""
        results: Dict[str, List] = {}
        results["vector"] = self.vector.search(query, top_k=top_k)
        results["semantic"] = self.semantic.query(subject=query.split()[0] if query else None)
        if self.long_term:
            results["long_term"] = self.long_term.retrieve(query, top_k=top_k)
        if self.episodic:
            results["episodic"] = self.episodic.retrieve(query, top_k=3)
        results["working"] = [i["content"] for i in self.working.all()[-top_k:]]
        return results

    def stats(self) -> Dict[str, Any]:
        return {
            "working": len(self.working),
            "vector": self.vector.count(),
            "semantic": len(self.semantic.all_facts()),
            "long_term": self.long_term.get_stats() if self.long_term and hasattr(self.long_term, "get_stats") else {},
            "episodic": len(self.episodic.get_recent(1000)) if self.episodic else 0,
        }

    def clear_all(self) -> None:
        self.working.clear()
        self.semantic.clear()
        self.vector.clear()
        if self.short_term:
            self.short_term.clear()
        if self.long_term:
            self.long_term.clear()
        if self.episodic:
            self.episodic.clear()
        logger.info("MemoryManager: all memories cleared.")
