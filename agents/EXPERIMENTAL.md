# Experimental agents

These are **not production**. They exist for architecture exploration.

| Type | Status |
|------|--------|
| `research` | Functional: retrieve + curriculum + optional LLM |
| `pev` | Thin: delegates execute to `react` |
| `reflexion` | Thin: ReasoningEngine 1–2 rounds |
| `vision` | Stub only – no VLM |
| `voice` | Stub only – no STT/TTS |
| `executor` | Helper / experimental |

Production agents: **`react`**, **`coding`** only.

```python
from agents.manager import agent_manager
agent = agent_manager.create("vision", allow_experimental=True)
# expect success=False with clear error for vision/voice stubs
```
