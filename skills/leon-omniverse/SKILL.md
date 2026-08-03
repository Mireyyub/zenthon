---
name: leon-omniverse
description: Leon AI Platform and NVIDIA Omniverse bridge workflows for Mireyyub/zenthon. Use when working on Leon cognitive stack, curriculum, reasoning, agents, planner, CLI/API/GUI, security sandbox, or Omniverse scene sync/ask/inject. Triggers include Leon, zenthon, Omniverse, ThinkingBrain, teach-volume, ReasoningEngine, ReAct sandbox.
---

# Leon + Omniverse

Repo: https://github.com/Mireyyub/zenthon  
AI identity: **Leon**. Cognitive path is primary; ML stack is optional/separate.

## When this skill applies

- Extend or debug Leon phases 0–9
- Curriculum teach/eval, reasoning traces, memory retrieve
- Production agents (`react`, `coding`) or planner
- Omniverse bridge (stub or live Kit)
- Security allowlist / path sandbox / audit

## Architecture (real)

```
CLI / GUI / FastAPI
  → BrainOrchestrator → ReasoningEngine
  → FactStore + Graph + Learning + Memory retrieve
  → Agents (react, coding sandbox) + Planner
  → tools (allowlist) + security gate
  → integrations/omniverse
```

Data root: `data/leon/` (override `LEON_DATA_DIR`).

## Essential commands

```bash
python -m interfaces.cli.main_cli start
python -m interfaces.cli.main_cli teach-volume 01
python -m interfaces.cli.main_cli reason "Daş mövcuddurmu?"
python -m interfaces.cli.main_cli health
python -m interfaces.cli.main_cli agent --list
python -m interfaces.cli.main_cli plan create --goal "öyrən" --curriculum 01
python -m interfaces.cli.main_cli omniverse status
python -m interfaces.cli.main_cli omniverse demo
python -m interfaces.cli.main_cli omniverse ask "Səhnədə hansı obyektlər var?"
uvicorn interfaces.api.main:app --port 8000
pytest tests/unit/test_facts_graph_learning.py tests/unit/test_security.py -q
bash scripts/ci_eval.sh
```

## Omniverse bridge

Module: `integrations/omniverse/bridge.py`

| Mode | Condition | Behavior |
|------|-----------|----------|
| stub | no omni/pxr | load_stub_demo_scene() |
| live | Kit available | sync_from_stage() |

```python
from integrations.omniverse import OmniverseBridge

ov = OmniverseBridge()
ov.load_stub_demo_scene()
ov.inject_scene_facts()
result = ov.ask_leon("Səhnədə neçə obyekt var?")
```

Rules:
- Never assume Kit is installed
- Always soft-fail to stub
- Scene facts go through FactStore with source=omniverse
- Security path tools only under data/leon/sandbox

## Security (Faza 9)

- Allowlist: security/allowlist.py — shell/network tools denied
- Path sandbox: write only data/leon/sandbox
- Audit: data/leon/audit/audit.jsonl
- Gate: tool_registry.dispatch calls gate_tool

```python
from security import safe_tool_call, tool_allowlist, audit_log
safe_tool_call("calc", "2+2")
```

## Production vs experimental

- Prod agents: react, coding
- Experimental: vision, voice, pev, reflexion — need allow_experimental=True
- See agents/EXPERIMENTAL.md

## Phase map

| Phase | Focus |
|-------|--------|
| 0–1 | bootstrap, persist |
| 2–3 | curriculum, unified reason |
| 4 | memory TTL, retrieve, quarantine |
| 5 | agents + safe tools |
| 6 | planner |
| 7 | CLI/GUI/API/health |
| 8 | tests, README realism, Omniverse |
| 9 | allowlist, path sandbox, audit |

## Coding conventions

- Persist under data/leon/{facts,graph,learning,memory,traces,plans,audit,sandbox}
- Prefer ReasoningEngine over ad-hoc LLM for curriculum questions
- Do not claim AGI; keep README claims = code
- Push to Mireyyub/zenthon main when implementing

## References

- references/cli-api.md — endpoint and CLI index
- references/omniverse.md — scene ops detail
