# 011 Memory Retrieval

`UnifiedRetriever.retrieve(query, top_k, min_score)`

Sources ranked with bonuses: fact > graph > semantic > vector.
Graph includes 1-hop and light 2-hop `is_a` chains.
Dedup by content prefix.
