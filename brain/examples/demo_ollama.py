"""
Ollama lokal LLM demo.

Əvvəlcə Ollama-nın işlədiyinə əmin ol:
    ollama serve
    ollama pull llama3.2

Sonra:
    python -m brain.examples.demo_ollama

İstəyə görə model dəyiş:
    export ZENTHON_LLM_MODEL=mistral
    export ZENTHON_LLM_MODEL=phi3
    export ZENTHON_LLM_MODEL=qwen2.5
"""

from brain import ThinkingBrain
from brain.llm import get_llm_client, use_ollama


def main():
    print("=" * 60)
    print("Zenthon Brain – Ollama Local LLM Demo")
    print("=" * 60)

    # Explicit Ollama
    client = use_ollama(model=os_model())
    health = client.health_check()

    print(f"Provider   : {health['provider']}")
    print(f"Base URL   : {health['base_url']}")
    print(f"Model      : {health['model']}")
    print(f"Reachable  : {health['reachable']}")
    if health.get("models"):
        print(f"Local models: {', '.join(health['models'][:8])}")
    if health.get("test_reply"):
        print(f"Test reply : {health['test_reply']}")

    if not health["reachable"]:
        print("\n[!] Ollama-ya qoşula bilmədi.")
        print("    1. ollama serve")
        print("    2. ollama pull llama3.2")
        print("    3. Yenidən bu skripti işə sal")
        return

    brain = ThinkingBrain(name="OllamaBrain", enable_meta=True)

    tests = [
        ("Süni intellektdə multimodal nə deməkdir? Qısa izah et.", "cot"),
        ("Kiçik bir chatbot layihəsi üçün 5 addımlı plan yaz.", "sot"),
    ]

    for q, mode in tests:
        print(f"\n--- {mode.upper()} ---")
        print(f"Sual: {q}")
        result = brain.think(q, goal="Faydalı və qısa cavab", reasoning_mode=mode)
        print(f"Confidence : {result['confidence']}")
        print(f"Decision   : {result['decision']['action']}")
        print(f"Conclusion : {result['conclusion'][:200]}")
        # llm_used bilgisini trace/metadata-dan göstər
        print(f"Modes tried: {result.get('modes_tried')}")

    print("\n" + "=" * 60)
    print("Demo bitdi.")


def os_model() -> str:
    import os
    return os.getenv("ZENTHON_LLM_MODEL", "llama3.2")


if __name__ == "__main__":
    main()
