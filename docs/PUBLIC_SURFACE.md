# Leon / Zenthon — Public Python Surface (Phase 2)

**Version:** 0.7.0 (cognitive prototype)  
**Rule:** Prefer these imports. Everything else is internal, experimental, or legacy.

---

## Canonical cognitive path

```
interfaces (CLI / FastAPI / GUI)
  → core.bootstrap / core.config / core.logger
  → brain.orchestrator.BrainOrchestrator
  → brain.reasoning.engine.ReasoningEngine
  → knowledge.registry + memory + curriculum + learning
  → agents.manager (react, coding)
  → security.gate.safe_tool_call
  → data/leon/
```

Do **not** call `ThinkingBrain` or ad-hoc LLM answerers for user queries.

---

## Public packages (stable for integrators)

| Package | Public symbols | Notes |
|---------|----------------|-------|
| `core` | `config`, `logger`, `event_bus`, `start_leon`, `leon_status`, `smoke_test`, `save_state`, `load_state` | Bootstrap + config |
| `core.contracts` | `Task`, `TaskStatus`, `EventName`, `AgentMessage`, … | Phase 1 domain contracts |
| `brain` | `BrainOrchestrator`, `reasoning_engine`, `ReasoningEngine` | Only public think path |
| `brain.llm` | `get_llm_client`, `get_llm_provider`, `LLMProvider`, `MockProvider` | Provider abstraction |
| `knowledge` | `get_fact_store`, `get_graph`, `FactStore`, `KnowledgeGraph` | Registry-backed |
| `memory` | `MemoryManager`, `retrieve`, `UnifiedRetriever`, `WorkingMemory`, `VectorMemory` | |
| `curriculum` | `CurriculumEngine`, `list_volumes`, `load_volume` | Volumes 01–07 |
| `learning` | `learning_engine`, `LearningEngine` | Promote only validated |
| `agents` | `agent_manager`, `BaseAgent`, `AgentResult` | Production: react, coding |
| `security` | `safe_tool_call`, `gate_tool`, `sandbox`, `tool_allowlist`, `audit_log` | Mandatory for tools |
| `tools` | `tool_registry` | Always via security gate |
| `interfaces.api.main` | `app` | FastAPI; default bind **127.0.0.1** |
| `interfaces.cli.main_cli` | CLI entry | |

---

## Internal (do not import from app code)

| Path | Role |
|------|------|
| `brain.core_brain.ThinkingBrain` | LLM backend only inside ReasoningEngine |
| `brain.core.Brain` | Thin compat stub |
| `brain.policy_bind` | Startup policy wiring |
| `brain.memory.*` | Prefer top-level `memory/` |
| Package-private helpers | `_`-prefixed modules/functions |

---

## Experimental

| Path | Flag |
|------|------|
| `agents.crew`, `agents.swarm` | Experimental multi-agent |
| `agents.vision_agent`, `agents.voice_agent` | Partial multimodal |
| `agents.local_agi.*` | Integrated; wiring into main cycle ongoing |

See `agents/EXPERIMENTAL.md`.

---

## Legacy (deprecated — still importable)

| Path | Use instead |
|------|-------------|
| `models/`, `training/`, `inference/predictors`, `inference/explainers` | Not part of cognitive core |
| `interfaces.web` | GUI / FastAPI |
| `inference.api.fastapi_app` | `interfaces.api.main` |
| Flask web entry | React UI (future) / current GUI |

Warnings: `core.deprecation.warn_legacy` / `@deprecated`.

---

## FastAPI route inventory (current, pre-/api/v1)

| Method | Path | Purpose |
|--------|------|--------|
| GET | `/` | Index + endpoint list |
| GET | `/health` | Health report |
| GET | `/status` | `leon_status()` |
| GET | `/native-core/status` | Native accelerator status |
| POST | `/think` | BrainOrchestrator.run |
| POST | `/reason` | ReasoningEngine.reason |
| POST | `/cycle` | CognitiveCycle (PODALR) |
| POST | `/crew` | Experimental crew |
| POST | `/orchestrate` | UnifiedAgentOrchestrator |
| POST | `/self-improve/sync` | Self-learning sync |
| POST | `/teach` | Curriculum teach |
| GET | `/volumes` | List curriculum volumes |
| POST | `/media/understand` | Image understand |
| POST | `/media/generate` | Procedural image gen |
| POST | `/audio` | STT/TTS/status |

**Target (Phase 3):** group under `/api/v1/*` without breaking these until a deprecation window.

**Default bind:** `127.0.0.1:8000` (LAN requires explicit host override).

---

## Network / offline policy

- Default API host: **127.0.0.1**
- Ollama expected local (`LEON_OLLAMA_HOST`)
- LLM failures must surface as `error` / unreachable — never silent success
- `MockProvider` for offline tests

Env: `LEON_API_HOST`, `LEON_API_PORT`, `LEON_DATA_DIR`, `LEON_LLM_*`, `LEON_ALLOW_MUTATE`

---

## Import smoke (integrators)

```python
from core import start_leon, config, logger
from brain import BrainOrchestrator, reasoning_engine
from knowledge import get_fact_store, get_graph
from memory import retrieve
from curriculum import CurriculumEngine
from agents import agent_manager
from security import safe_tool_call
from core.contracts import Task, EventName, AgentMessage
from brain.llm import get_llm_provider
```

---

*Phase 2 — isolation only. No cognitive behavior change.*
