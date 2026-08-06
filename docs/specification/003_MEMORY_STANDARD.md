# 003 Memory Standard

Layers:
1. **Working** – capacity + TTL, unverified claims
2. **Vector** – hybrid BOW/dense search, disk JSON
3. **Semantic** – subject-predicate-object triples
4. **Episodic / long-term** – optional brain.memory

Promotion: only after LearningEngine validated → `MemoryManager.promote_validated`.

Retrieval: `memory.retrieve.UnifiedRetriever` (facts + graph + vector + semantic).
