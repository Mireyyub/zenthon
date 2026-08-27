"""VectorMemory tests (BOW path)."""

from memory.vector_memory import VectorMemory


def test_add_and_search_bow(tmp_path):
    vm = VectorMemory(use_llm_embeddings=False, path=tmp_path / "vector.json")
    vm.add("Leon AI platform uses Ollama for local inference")
    vm.add("Random forest is a supervised learning algorithm")
    hits = vm.search("Ollama local Leon", top_k=2)
    assert len(hits) >= 1
    assert "Leon" in hits[0][0] or "Ollama" in hits[0][0]


def test_count_and_clear(tmp_path):
    vm = VectorMemory(use_llm_embeddings=False, path=tmp_path / "vector.json")
    vm.add("hello world")
    assert vm.count() == 1
    vm.clear()
    assert vm.count() == 0
