---
name: leon-omniverse
description: Leon AI Platform (Mireyyub/zenthon) and NVIDIA Omniverse bridge. Use for Leon cognitive stack, curriculum, ReasoningEngine, agents, planner, CLI/API/GUI, security sandbox, Omniverse scene sync/ask/inject, teach-volume, GraphRAG, and phase 0-9 work on the zenthon repo.
---

# Leon + Omniverse

Repo: https://github.com/Mireyyub/zenthon  
Identity: **Leon**. Cognitive path primary; ML stack optional/legacy.

## Activate when

- User works on Leon, zenthon, ThinkingBrain, curriculum, Omniverse
- CLI/API/GUI, agents, planner, security, phases 0-9
- Persist under `data/leon/`, Ollama local LLM

## Architecture

```
CLI / GUI / FastAPI (interfaces.api.main)
  → BrainOrchestrator → ReasoningEngine
  → FactStore + Graph + Learning + Memory retrieve
  → Agents (react, coding) + Planner
  → tools allowlist + security gate
  → integrations/omniverse
```

## Commands (canonical)

```bash
python -m interfaces.cli.main_cli start [--bootstrap]
python -m interfaces.cli.main_cli teach-volume 01
python -m interfaces.cli.main_cli reason "Daş mövcuddurmu?"
python -m interfaces.cli.main_cli health
python -m interfaces.cli.main_cli agent --list
python -m interfaces.cli.main_cli plan create --goal "öyrən" --curriculum 01
python -m interfaces.cli.main_cli omniverse status|demo|ask "..."
uvicorn interfaces.api.main:app --port 8000
pytest tests/unit/test_facts_graph_learning.py tests/unit/test_security.py -q
bash scripts/ci_eval.sh
```

## Omniverse

```python
from integrations.omniverse import OmniverseBridge
ov = OmniverseBridge()
ov.load_stub_demo_scene()
ov.inject_scene_facts()
ov.ask_leon("Səhnədə neçə obyekt var?")
```

Rules: never assume Kit; soft-fail stub; facts via FactStore; paths only under `data/leon/sandbox`.

## Security (phase 9)

- Allowlist in `security/allowlist.py`
- Write sandbox: `data/leon/sandbox`
- Audit JSONL: `data/leon/audit/audit.jsonl`
- Use `safe_tool_call` / `gate_tool`

## Production vs experimental

- Prod agents: `react`, `coding`
- Prefer `interfaces.api.main` over legacy inference API

## Conventions

- Persist under `data/leon/`
- Prefer ReasoningEngine for curriculum Q&A
- Push to `Mireyyub/zenthon` `main`
