# Leon / Zenthon — Public Python Surface

**Version:** 0.8.0 Alpha  
**Rule:** Prefer these imports. Everything else is internal, experimental, or legacy.

---

## Canonical cognitive path

```
interfaces (CLI / FastAPI / GUI) + ui/ (React client)
  → core.bootstrap / core.config / core.logger
  → brain.orchestrator.BrainOrchestrator
  → brain.reasoning.engine.ReasoningEngine
  → knowledge.registry + memory + curriculum + learning
  → brain.llm.get_llm_provider()
  → agents.manager (react, coding)
  → security.gate.safe_tool_call
  → data/leon/
```

Do **not** call `ThinkingBrain` for user queries.

---

## Public packages

| Package | Public symbols | Notes |
|---------|----------------|-------|
| `core` | `config`, `logger`, `event_bus`, `start_leon`, `leon_status`, `smoke_test`, `save_state`, `load_state` | Bootstrap |
| `core.contracts` | `Task`, `TaskStatus`, `EventName`, `AgentMessage`, … | Domain contracts |
| `core.supervisor` | `ProcessSupervisor`, `supervisor_status` | API process management |
| `core.storage` | SQLite helpers, migrate | Tasks durable |
| `brain` | `BrainOrchestrator`, `ReasoningEngine` | Only public think path |
| `brain.llm` | `get_llm_provider`, `LLMProvider`, `MockProvider` | Provider primary |
| `brain.rag` | `RAGPipeline` | Partial; disk under `data/leon/rag` |
| `knowledge` | `get_fact_store`, `get_graph`, `FactStore`, `KnowledgeGraph` | Registry |
| `memory` | `MemoryManager`, `retrieve`, `UnifiedRetriever`, `WorkingMemory`, `VectorMemory` | |
| `curriculum` | `CurriculumEngine`, `list_volumes`, `load_volume` | |
| `learning` | `LearningEngine` | Promote only validated |
| `agents` | `agent_manager`, `BaseAgent`, `AgentResult` | Production: react, coding |
| `security` | `safe_tool_call`, `gate_tool`, `sandbox`, `tool_allowlist`, `audit_log` | Mandatory for tools |
| `tools` | `tool_registry` | Via security gate |
| `native_core` | `get_native_core`, `desktop_status` | Readiness honest |
| `interfaces.api.main` | `app` | Default bind **127.0.0.1** |
| `interfaces.cli.main_cli` | CLI entry | |
| `leon_desktop` | `run_desktop` | Supervisor + GUI entry |

---

## HTTP API

**Prefer:** `/api/v1/*`  
**Default bind:** `127.0.0.1:8000` (`LEON_API_HOST`, `LEON_API_PORT`)

| Method | Path | Purpose |
|--------|------|--------|
| GET | `/api/v1/` | v1 index |
| GET | `/api/v1/health` | Health |
| GET | `/api/v1/status` | `leon_status()` |
| GET | `/api/v1/system/desktop` | Desktop readiness (honest flags) |
| GET | `/api/v1/system/supervisor` | Supervisor probe |
| GET | `/api/v1/native-core/status` | Native / fallback |
| POST | `/api/v1/chat` | Orchestrator chat |
| POST | `/api/v1/think` | Orchestrator.run |
| POST | `/api/v1/reason` | ReasoningEngine.reason |
| POST | `/api/v1/cycle` | CognitiveCycle |
| GET | `/api/v1/agents` | List agents |
| POST | `/api/v1/agents/run` | Single agent |
| POST | `/api/v1/agents/orchestrate` | Multi agent |
| GET/POST | `/api/v1/tasks` | Durable tasks |
| POST | `/api/v1/memory/retrieve` | Unified retrieve |
| GET | `/api/v1/knowledge/facts` | Fact sample |
| GET | `/api/v1/knowledge/graph` | Graph stats |
| GET | `/api/v1/volumes` | Curriculum |
| POST | `/api/v1/teach` | Teach |
| POST | `/api/v1/self/improve` | Self-learning |
| GET | `/api/v1/self/view` | Body map |
| GET | `/api/v1/models` | LLMProvider health |
| GET | `/api/v1/tools` | Tool names |
| POST | `/api/v1/tools/call` | `safe_tool_call` only |
| POST | `/api/v1/media/*` | Multimodal |
| WS | `/ws` | Typed events |

OpenAPI: `http://127.0.0.1:8000/docs`

**LAN:** only if user sets `LEON_API_HOST=0.0.0.0` deliberately.

---

## Internal / experimental / legacy

See `LEGACY.md`, `agents/EXPERIMENTAL.md`, `docs/DESKTOP.md`.

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
from native_core import desktop_status
from core.supervisor import supervisor_status
```

---

*Wave A: documentation honesty — claims match code. No cognitive rewrite.*
