"""
LLM inteqrasiyası demo.

Əvvəlcə environment variable təyin et:

    export ZENTHON_LLM_API_KEY="sk-..."
    export ZENTHON_LLM_BASE_URL="https://api.openai.com/v1"   # və ya xAI
    export ZENTHON_LLM_MODEL="gpt-4o-mini"

Sonra:
    python -m brain.examples.demo_llm
"""

from brain import ThinkingBrain
from brain.llm import get_llm_client


def main():
    client = get_llm_client()
    print("=" * 60)
    print("Zenthon Brain – LLM Integration Demo")
    print("=" * 60)
    print(f"LLM available : {client.is_available}")
    print(f"Model         : {client.config.model}")
    print(f"Base URL      : {client.config.base_url}")

    if not client.is_available:
        print("\n[!] API key tapılmadı.")
        print("    export ZENTHON_LLM_API_KEY=your_key")
        print("    export ZENTHON_LLM_BASE_URL=https://api.x.ai/v1   # Grok üçün")
        print("    export ZENTHON_LLM_MODEL=grok-3")
        print("\nFallback (qayda əsaslı) rejimində davam edir...")

    brain = ThinkingBrain(name="LLMBrain", enable_meta=True)

    questions = [
        ("Süni intellektdə multimodal nə deməkdir?", "cot"),
        ("CNN ilə Transformer-i müqayisə et, hansını seçərdin?", "tot"),
        ("Kiçik multimodal AI prototipi qurmaq üçün plan hazırla.", "sot"),
    ]

    for q, mode in questions:
        print(f"\n--- Mode: {mode} ---")
        print(f"Sual: {q}")
        result = brain.think(q, goal="Aydın və faydalı cavab", reasoning_mode=mode)
        print(f"LLM used   : {result.get('trace') and 'llm_used' in str(result)}")
        print(f"Confidence : {result['confidence']}")
        print(f"Decision   : {result['decision']['action']}")
        print(f"Conclusion : {result['conclusion'][:160]}...")

    print("\n" + "=" * 60)
    print("Demo bitdi.")


if __name__ == "__main__":
    main()
