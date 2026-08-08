# Experimental agents

| Type | Status |
|------|--------|
| `research` | Functional: retrieve + curriculum + optional LLM |
| `pev` | Thin: delegates execute to `react` |
| `reflexion` | Thin: ReasoningEngine 1–2 rounds |
| `vision` | **Image ops + procedural generate + optional Ollama VLM describe** |
| `voice` | Stub only – no STT/TTS |
| `executor` | Helper / experimental |

Production agents: **`react`**, **`coding`** only.

## Vision

```bash
pip install Pillow
ollama pull llava   # optional describe

python -m interfaces.cli.main_cli image status
python -m interfaces.cli.main_cli image generate --style shapes --prompt "demo"
python -m interfaces.cli.main_cli image info path/to.png
python -m interfaces.cli.main_cli image describe path/to.png
python -m interfaces.cli.main_cli agent vision "generate gradient night" --experimental
```

- **process / info / generate**: local Pillow (sandbox `data/leon/sandbox/images`)
- **describe**: Ollama vision model; missing model → clear error, not fake success
