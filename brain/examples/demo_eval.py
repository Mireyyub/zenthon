"""
Evaluation + GraphRAG demo.

    python -m brain.examples.demo_eval
"""

import json
from evaluation import evaluate_brain
from knowledge.graphrag import GraphRAG


def main():
    print("=" * 60)
    print("Zenthon Evaluation + GraphRAG Demo")
    print("=" * 60)

    # GraphRAG ingest + retrieve
    print("\n--- GraphRAG ---")
    gr = GraphRAG()
    gr.ingest(
        "Zenthon modul əsaslı AI platformasıdır və Ollama ilə lokal işləyir.",
        entities=["Zenthon", "Ollama", "AI"],
    )
    gr.ingest(
        "RAG retrieval-augmented generation texnikasıdır.",
        entities=["RAG", "retrieval", "generation"],
    )
    ctx = gr.as_context_block("Zenthon lokal")
    print(ctx or "(empty context)")
    print("Combined:", gr.retrieve("RAG")["combined"][:3])

    # Benchmark
    print("\n--- Brain Benchmark ---")
    summary = evaluate_brain(limit=3)
    print(json.dumps(summary, ensure_ascii=False, indent=2, default=str))

    print("=" * 60)


if __name__ == "__main__":
    main()
