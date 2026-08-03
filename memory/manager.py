"""Memory Manager – layers + promotion + unified retrieve (Faza 4)."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from core.logger import logger
from core.event_bus import event_bus
from memory.working_memory import WorkingMemory
from memory.semantic import SemanticMemory
from memory.vector_memory import VectorMemory
from memory.retrieve import UnifiedRetriever

try:
    from brain.memory.short_term import ShortTermMemory
    from brain.memory.long_term import LongTermMemory
    from brain.memory.episodic import EpisodicMemory
except ImportError:
    ShortTermMemory = LongTermMemory = EpisodicMemory = None


class MemoryManager:
    """Vahid yaddaş interfeysi."""

    def __init__(self, working_capacity: int = 32, working_ttl: int = 1800):
        self.working = WorkingMemory(capacity=working_capacity, ttl_seconds=working_ttl)
        self.semantic = SemanticMemory()
        self.vector = VectorMemory()
        self.short_term = ShortTermMemory() if ShortTermMemory else None
        self.long_term = LongTermMemory() if LongTermMemory else None
        self.episodic = EpisodicMemory() if EpisodicMemory else None
        self._retriever = UnifiedRetriever()
        logger.info("MemoryManager initialized (Faza 4).")

    def remember(self, text: str, kind: str = "vector", **kwargs) -> str:
        """
        kind:
          working | vector | semantic | long_term | episodic
          verified=True (default) — validated bilik
        """
        verified = kwargs.get("verified", True)
        if kind == "semantic":
            return self.semantic.store_fact(
                kwargs.get("subject", text),
                kwargs.get("predicate", "is"),
                kwargs.get("object", "known"),
                kwargs.get("confidence", 1.0),
            )
        if kind == "working":
            return self.working.add(
                text, tag=kwargs.get("tag", "general"), importance=kwargs.get("importance", 0.5)
            )
        if kind == "long_term" and self.long_term:
            return self.long_term.store(kwargs.get("key", text[:40]), text)
        if kind == "episodic" and self.episodic:
            try:
                return self.episodic.store(text, metadata=kwargs.get("metadata") or {})
            except Exception:
                pass
        # default vector – yalnız verified (promotion path)
        if not verified and kind == "vector":
            # unverified yalnız working-ə
            return self.working.add(text, tag="unverified", importance=0.3)
        doc_id = self.vector.add(text, metadata=kwargs.get("metadata"))
        event_bus.publish("MemoryUpdated", {"kind": kind, "id": doc_id}, source="memory")
        return doc_id

    def promote_validated(
        self,
        content: str,
        *,
        source: str = "learning",
        confidence: float = 0.8,
        learning_id: str = "",
        to_semantic: bool = True,
        to_vector: bool = True,
        to_episodic: bool = True,
    ) -> Dict[str, Any]:
        """Yalnız LearningEngine validated sonrası çağırılmalıdır."""
        out: Dict[str, Any] = {"content": content[:120], "actions": []}
        meta = {"source": source, "confidence": confidence, "learning_id": learning_id, "verified": True}

        if to_vector:
            try:
                vid = self.vector.add(content, metadata=meta)
                out["actions"].append({"layer": "vector", "id": vid})
            except Exception as e:
                out["actions"].append({"layer": "vector", "error": str(e)})

        if to_semantic:
            try:
                # sadə triple: content as object of "learned"
                fid = self.semantic.store_fact("Leon", "learned", content[:200], confidence=confidence)
                out["actions"].append({"layer": "semantic", "id": fid})
            except Exception as e:
                out["actions"].append({"layer": "semantic", "error": str(e)})

        if to_episodic and self.episodic:
            try:
                eid = self.episodic.store(content, metadata=meta)
                out["actions"].append({"layer": "episodic", "id": eid})
            except Exception as e:
                out["actions"].append({"layer": "episodic", "error": str(e)})

        # working-dən unverified təmizləmə cəhdi
        try:
            for item in list(self.working.get_by_tag("unverified")):
                if str(item.get("content"))[:80] == content[:80]:
                    # cannot delete by id easily if no API – skip
                    pass
        except Exception:
            pass

        event_bus.publish("MemoryPromoted", out, source="memory")
        logger.info(f"Memory promote: {len(out['actions'])} layers")
        return out

    def recall(self, query: str, top_k: int = 5) -> Dict[str, List]:
        results: Dict[str, List] = {}
        results["vector"] = self.vector.search(query, top_k=top_k)
        results["semantic"] = self.semantic.query(subject=query.split()[0] if query else None)
        if self.long_term:
            results["long_term"] = self.long_term.retrieve(query, top_k=top_k)
        if self.episodic:
            try:
                results["episodic"] = self.episodic.retrieve(query, top_k=3)
            except Exception:
                results["episodic"] = []
        results["working"] = [i["content"] for i in self.working.all()[-top_k:]]
        return results

    def retrieve(self, query: str, top_k: int = 8, **kw) -> Dict[str, Any]:
        """Vahid ranked retrieval."""
        return self._retriever.retrieve(query, top_k=top_k, **kw)

    def stats(self) -> Dict[str, Any]:
        return {
            "working": self.working.stats() if hasattr(self.working, "stats") else len(self.working),
            "vector": self.vector.count(),
            "semantic": len(self.semantic.all_facts()),
            "long_term": self.long_term.get_stats()
            if self.long_term and hasattr(self.long_term, "get_stats")
            else {},
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
