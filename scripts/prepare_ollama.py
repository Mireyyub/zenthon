"""Check and optionally prepare the configured local Ollama service."""

from __future__ import annotations

import json


def main() -> int:
    from brain.llm.ollama_manager import ensure_ollama

    print(json.dumps(ensure_ollama(), ensure_ascii=False, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
