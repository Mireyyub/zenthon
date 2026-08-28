# Leon / Zenthon — Public Python Surface (Phase 2–3)

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

## HTTP API (Phase 3)

**Prefer:** `/api/v1/*`  
**Legacy:** root paths still work (compatibility).

| Method | Path | Purpose |
|--------|------|--------|
| GET | `/api/v1/` | v1 index |
| GET | `/api/v1/health` | Health report |
| GET | `/api/v1/status` | `leon_status()` |
| POST | `/api/v1/chat` | UI chat → Orchestrator |
| POST | `/api/v1/think` | Orchestrator.run |
| POST | `/api/v1/reason` | ReasoningEngine.reason |
| POST | `/api/v1/cycle` | CognitiveCycle |
| GET | `/api/v1/agents` | List agents |
| POST | `/api/v1/agents/run` | Single agent |
| POST | `/api/v1/agents/orchestrate` | Multi agent |
| GET/POST | `/api/v1/tasks` | In-memory tasks (not durable yet) |
| POST | `/api/v1/memory/retrieve` | Unified retrieve |
| GET | `/api/v1/knowledge/facts` | Fact sample |
| GET | `/api/v1/knowledge/graph` | Graph stats |
| GET | `/api/v1/volumes` | Curriculum volumes |
| POST | `/api/v1/teach` | Teach lesson/volume |
| POST | `/api/v1/self/improve` | Self-learning sync |
| GET | `/api/v1/self/view` | High-level body map |
| GET | `/api/v1/models` | LLM provider health |
| GET | `/api/v1/tools` | Tool names (gated) |
| POST | `/api/v1/tools/call` | `safe_tool_call` only |
| POST | `/api/v1/media/*` | Multimodal |

OpenAPI: `http://127.0.0.1:8000/docs`

**Default bind:** `127.0.0.1:8000`  
Env: `LEON_API_HOST`, `LEON_API_PORT`

---

## Internal / experimental / legacy

See `LEGACY.md` and `agents/EXPERIMENTAL.md`.

---

## Import smoke

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

*Phase 2 isolation + Phase 3 /api/v1. No cognitive behavior change.*
