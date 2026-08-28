# ARCHITECTURE_AUDIT.md

**Repo:** Mireyyub/zenthon  
**Identity:** Leon  
**Current declared version:** v0.7 cognitive prototype  
**Audit date:** 2026-08-28  
**Target:** Hybrid Local Multi-Language Production-Grade Desktop AI Platform (Windows 11 first)  
**Rule applied:** Do not rewrite from scratch. Keep working core. Phase 0 = audit only.

---

## 0. Executive summary (real state)

| Layer | Current reality | Target reality |
|-------|-----------------|----------------|
| Cognitive core | Strong Python monolith (ReasoningEngine, Curriculum, Memory, Agents, Planner, Security, Self*) | Keep as Python cognitive brain |
| API | FastAPI (`interfaces/api/main.py`) + some legacy Flask | FastAPI v1 gateway, 127.0.0.1 only by default |
| UI | Tkinter GUI + legacy Flask web | React + TypeScript (Vite + Tailwind) |
| Desktop shell | Python scripts + NSIS stub + partial native_core Rust | Tauri + Rust process supervisor |
| Persistence | Mostly JSON under `data/leon/` + optional SQLite sketch | SQLite (SQLAlchemy) + migration from JSON |
| LLM | Direct Ollama client usage | LLMProvider abstraction (Ollama / Mock / Future) |
| Agents | Multiple families (react/coding + local_agi + crew/swarm + skills) | Unified AgentManager + Task Engine + Blackboard |
| Security | Allowlist + PathSandbox + gate + audit JSONL | Keep and harden; never bypass |
| Packaging | `scripts/build_windows.ps1` + NSIS | Zenthon.exe + Zenthon-Setup.exe (Tauri) |
| Offline-first | Mostly yes (Ollama local) | Explicit OFFLINE status, no silent network failure |
| Tests | Good unit/integration coverage for cognitive path | Expand to TS/Rust/E2E |

**Honest assessment:** The cognitive Python core is the most mature and valuable part of the repository. Desktop, multi-language runtime, durable task engine, full RAG pipeline, and modern UI are either partial, experimental, or missing. The project is **not** yet a production Windows 11 desktop platform. It is a solid offline-first cognitive prototype with honest claims in README/ARCHITECTURE.

---

## 1. Repository map (high level)

```
zenthon/
├── brain/              # Cognitive core (KEEP)
├── agents/             # Agent families + local_agi + skills (KEEP + unify)
├── core/               # Bootstrap, config, logger, event bus (KEEP)
├── knowledge/          # Facts, Graph, GraphRAG, registry (KEEP)
├── memory/             # Working/episodic/semantic/vector (KEEP + modernize)
├── curriculum/         # Volumes 01–07 (KEEP)
├── learning/           # LearningEngine (KEEP)
├── security/           # Gate, sandbox, allowlist, audit (KEEP + harden)
├── tools/              # Registry, engine, domain, safe_fs (KEEP)
├── multimodal/         # Image/audio/vision (partial, honest stubs where needed)
├── interfaces/
│   ├── api/            # FastAPI (KEEP → expand to /api/v1)
│   ├── cli/            # Rich CLI (KEEP)
│   ├── gui/            # Tkinter (LEGACY for desktop UI target)
│   ├── web/            # Flask (LEGACY)
│   └── websocket/      # Thin server (KEEP → expand events)
├── integrations/omniverse/  # Bridge (KEEP, optional)
├── native_core/        # Python adapter + small Rust crate (KEEP as seed for Tauri)
├── data/leon/          # Runtime JSON persistence (MIGRATE carefully)
├── models/, training/, inference/  # Classic ML demos (LEGACY)
├── evaluation/, genome/, schemas/, prompts/
├── docs/, scripts/, tests/, windows/
├── run.py, zenthon_app.py, zenthon_desktop.py
└── requirements.txt, pyproject.toml (needs alignment)
```

Approx. **521** tracked paths. Dominant language: **Python**. Minimal Rust (`native_core/rust/zenthon-native-core`). No React/TypeScript/Tauri yet.

---

## 2. Module-by-module audit

Format: **MODUL | MƏQSƏDİ | DİL | STATUS | ASILIQLAR | İSTİFADƏ EDƏNLƏR | PROBLEM | QƏRAR**

### 2.1 Cognitive core (KEEP)

| Modul | Məqsəd | Dil | Status | Asılılıqlar | İstifadə edənlər | Problem | Qərar |
|-------|--------|-----|--------|-------------|------------------|---------|-------|
| `brain/orchestrator.py` | BrainOrchestrator — single entry | Python | İşlək | ReasoningEngine, agents, security | CLI, API, GUI | — | KEEP |
| `brain/reasoning/engine.py` | ReasoningEngine (evidence, conflict→UNKNOWN, trace) | Python | İşlək | knowledge, memory, curriculum, LLM | Orchestrator | Strong path; LLM not fully abstracted | KEEP + LLMProvider |
| `brain/cognitive_cycle.py` | PODALR cycle | Python | İşlək | Multiple brain modules | Orchestrator / CLI | Needs AgentManager wiring | KEEP + wire |
| `brain/planning/planner.py` + `dag_runner.py` | Planner + topo order | Python | İşlək | schema, data/leon/plans | CLI plan | Not durable Task Engine | KEEP; extend to Task Engine |
| `brain/self_view.py` | Introspection | Python | İşlək | AST, path policy | CLI self | Restricted FS good | KEEP + expand safe surface |
| `brain/self_improve.py` | Multi-round improve | Python | İşlək | curriculum, green-gate | CLI improve | Large file; needs tests | KEEP |
| `brain/self_mutate.py` | Allowlisted mutation | Python | İşlək (gated) | allowlist, LEON_ALLOW_MUTATE | CLI mutate | Correctly restricted | KEEP; never unrestricted |
| `brain/system_loop.py` | System status/improve | Python | İşlək | self_* | CLI system | — | KEEP |
| `brain/llm/client.py` + `async_client.py` | Ollama client | Python | İşlək | httpx, ollama | ReasoningEngine | Direct Ollama coupling | Abstract behind LLMProvider |
| `brain/llm/cache.py` | LRU cache | Python | İşlək | — | LLM client | — | KEEP |
| `brain/rag/pipeline.py` | Basic RAG | Python | Partial | memory/vector | Reasoning path | Not full Document→Reranker pipeline | Expand |
| `brain/world_state.py` | World state | Python | İşlək | — | Long-horizon | — | KEEP |
| `brain/core_brain.py` | ThinkingBrain (LLM backend) | Python | Internal | LLM | ReasoningEngine only | Must stay internal | KEEP internal |
| `brain/core.py` | Thin Brain stub | Python | Legacy compat | — | Imports | Stub | KEEP for compat |

### 2.2 Knowledge & Memory (KEEP + modernize)

| Modul | Məqsəd | Dil | Status | Asılılıqlar | İstifadə | Problem | Qərar |
|-------|--------|-----|--------|-------------|----------|---------|-------|
| `knowledge/facts.py` + registry | FactStore | Python | İşlək | disk JSON | Reasoning, Learning | JSON only | KEEP; migrate to SQLite later |
| `knowledge/graph.py` | Knowledge graph | Python | İşlək | JSON | Reasoning, GraphRAG | — | KEEP |
| `knowledge/graphrag.py` | GraphRAG | Python | İşlək | UnifiedRetriever | Reasoning | — | KEEP |
| `memory/working_memory.py` | TTL working memory | Python | İşlək | — | Retrieve | — | KEEP |
| `memory/vector_memory.py` | Hybrid dense+bow | Python | İşlək | numpy | Retrieve | No full embedding model abstraction | KEEP + improve |
| `memory/manager.py` + `retrieve.py` | Unified retrieve | Python | İşlək | facts/graph/vector | Orchestrator | — | KEEP |
| `learning/engine.py` | Learning + validation | Python | İşlək | registry | Curriculum, promote | — | KEEP |

### 2.3 Agents (KEEP + unify)

| Modul | Məqsəd | Dil | Status | Asılılıqlar | İstifadə | Problem | Qərar |
|-------|--------|-----|--------|-------------|----------|---------|-------|
| `agents/manager.py` | Agent registry | Python | İşlək | react, coding | Orchestrator | Multiple agent families coexist | Unify under AgentManager |
| `agents/react_agent.py` | ReAct | Python | Production | tools, security | Manager | — | KEEP |
| `agents/coding_agent.py` | Coding (templates + filter) | Python | Production | tools | Manager | Offline templates good | KEEP |
| `agents/research_agent.py` | Research | Python | Functional | — | Manager | — | KEEP |
| `agents/local_agi/*` | Base + Planner/Reasoning/Critic/Execution/Memory | Python | Integrated from Drive | BaseAgent | Partial wiring | Not fully in cognitive cycle | Wire into cycle |
| `agents/skills/*` | Skill registry (LEON-mega port) | Python | Integrated | — | tools/engine | — | KEEP |
| `agents/crew.py` + `swarm.py` | Multi-agent patterns | Python | Experimental | blackboard | Optional | Experimental flag | Flag experimental |
| `agents/blackboard.py` | Shared board | Python | İşlək | — | Crew/swarm | — | KEEP for multi-agent |
| `agents/vision_agent.py` / `voice_agent.py` | Multimodal agents | Python | Partial / honest | multimodal | Optional | Not full production | Honest status |

### 2.4 Security (KEEP + harden)

| Modul | Məqsəd | Dil | Status | Asılılıqlar | İstifadə | Problem | Qərar |
|-------|--------|-----|--------|-------------|----------|---------|-------|
| `security/gate.py` | safe_tool_call | Python | İşlək | allowlist, sandbox, audit | All tools | — | KEEP |
| `security/sandbox.py` | PathSandbox | Python | İşlək | — | Gate | — | KEEP |
| `security/allowlist.py` | Tool allowlist | Python | İşlək | — | Gate | — | KEEP |
| `security/audit.py` | JSONL audit | Python | İşlək | data/leon/audit | Gate | — | KEEP |
| `security/permissions.py` | Permission model | Python | Partial | — | Gate | Expand for FS/shell/network | Expand |

### 2.5 Interfaces

| Modul | Məqsəd | Dil | Status | Asılılıqlar | İstifadə | Problem | Qərar |
|-------|--------|-----|--------|-------------|----------|---------|-------|
| `interfaces/api/main.py` | FastAPI | Python | İşlək | orchestrator | External | Not full /api/v1; host often 0.0.0.0 | Expand + default 127.0.0.1 |
| `interfaces/cli/main_cli.py` | Rich CLI | Python | İşlək | all core | Dev/ops | — | KEEP |
| `interfaces/gui/main_gui.py` | Tkinter GUI | Python | İşlək | orchestrator | Desktop today | Not modern UI | LEGACY for target UI |
| `interfaces/web/web_interface.py` | Flask | Python | Deprecated | — | Legacy | Deprecated | Deprecate → remove after migration |
| `interfaces/websocket/server.py` | WS | Python | Thin | — | Events | Incomplete event model | Expand to typed events |

### 2.6 Tools & Domain

| Modul | Məqsəd | Dil | Status | Asılılıqlar | İstifadə | Problem | Qərar |
|-------|--------|-----|--------|-------------|----------|---------|-------|
| `tools/registry.py` | Tool registry + security | Python | İşlək | security | Agents | — | KEEP |
| `tools/engine.py` | ToolEngine (v10) | Python | Integrated | domain, skills | Agents | — | KEEP |
| `tools/domain/math_ops.py` + `chemistry.py` | AgilBot safe subset | Python | Integrated | — | Engine | — | KEEP |
| `tools/safe_fs.py` | Sandboxed FS | Python | İşlək | security | Tools | — | KEEP |

### 2.7 Curriculum & Evaluation

| Modul | Status | Qərar |
|-------|--------|-------|
| `curriculum/` Volumes 01–07 | İşlək (Foundation strongest) | KEEP |
| `evaluation/` (benchmark, transfer, human_suite) | İşlək | KEEP |
| `genome/` | Present | KEEP |

### 2.8 Multimodal

| Modul | Status | Qərar |
|-------|--------|-------|
| `multimodal/image_ops.py`, `vision.py`, `understand.py`, `generate.py`, `audio.py` | Partial; local stats + VLM multi-pass where possible; honest stubs | KEEP + honesty |

### 2.9 Native / Desktop seeds

| Modul | Status | Qərar |
|-------|--------|-------|
| `native_core/adapter.py` + Rust crate | Small deterministic ops + Python fallback | Seed for Tauri/Rust runtime; do not expand AI logic into Rust |
| `windows/Zenthon.nsi` + `scripts/build_windows.ps1` | Basic NSIS packaging | Replace with Tauri packaging |
| `zenthon_desktop.py` | Thin | Will be superseded |

### 2.10 Legacy / optional (do not delete yet)

| Path | Status | Qərar |
|------|--------|-------|
| `models/`, `training/`, `inference/predictors`, `inference/explainers` | Classic ML demos; deprecation warnings | LEGACY — do not import from cognitive path |
| `interfaces/web` | Flask | Deprecate after React UI |
| `inference/api/fastapi_app.py` | Re-export | Deprecate |
| `brain.core.Brain` | Stub | Compat only |

---

## 3. Working modules (production-grade within prototype)

- Core bootstrap + config + logger
- Knowledge registry (FactStore / Graph / Learning / Vector)
- ReasoningEngine single path + evidence + conflict → UNKNOWN + traces
- Curriculum Volumes + teach/eval
- Memory (working + vector hybrid + promote_validated)
- Production agents: react, coding
- Planner + DAG runner
- Security gate + PathSandbox + allowlist + audit
- SelfView / SelfImprove / gated SelfMutate
- CLI surface
- FastAPI basic surface
- Omniverse bridge (optional)
- Unit + integration tests for cognitive path

---

## 4. Experimental modules

- `agents/crew.py`, `agents/swarm.py` (flagged)
- Vision/voice agents (honest incomplete multimodal)
- Full multi-agent blackboard orchestration in main cycle (partial)
- `tools/domain` chemistry/math beyond safe subset

---

## 5. Legacy / deprecated

- `models/`, `training/`, classic `inference/` demos
- Flask `interfaces/web`
- `inference/api/fastapi_app.py` re-export
- Tkinter as long-term desktop UI (still functional today)

---

## 6. Duplicate / parallel implementations

| Area | Observation | Decision |
|------|-------------|----------|
| Reasoning | Single public path (good). ThinkingBrain internal only | Maintain single path |
| Agents | `agents/*` + `agents/local_agi/*` + skills | Unify under one AgentManager; keep local_agi as implementations |
| Memory | `brain/memory/*` vs `memory/*` | Prefer top-level `memory/` as public; brain.memory as internal helpers if still used |
| API | FastAPI main vs legacy Flask/re-export | Canonical = `interfaces.api.main` |
| Event bus | `core/event_bus.py` + `core/async_event_bus.py` | Unify into typed event model |

---

## 7. Circular dependency risks

- Registry singletons (`knowledge.registry`, agent manager) reduce cycles — good.
- Orchestrator → agents → tools → security → (possible) orchestrator feedback: currently controlled via gate.
- Self-mutate → import → cognitive modules: restricted by allowlist; risk if allowlist widened.
- **Monitor:** `brain` ↔ `agents` ↔ `tools` import graph during AgentManager unification.

---

## 8. Security risks (current)

| Risk | Severity | Mitigation status |
|------|----------|-------------------|
| Tool execution without gate | High | Gate present — must remain mandatory |
| Self-mutate unrestricted | High | Default `LEON_ALLOW_MUTATE=false` + allowlist |
| API bind 0.0.0.0 | Medium | Change default to 127.0.0.1 |
| Agent unrestricted FS/shell | High | Sandbox + allowlist — keep |
| Secrets in logs | Medium | Structured logging policy needed |
| Native binary trust | Medium | native_core already has fallback + allowlist ops |

---

## 9. Performance issues

- JSON file persistence under load (many small writes) — SQLite migration will help.
- LLM calls without strong provider-level concurrency control.
- GUI (Tkinter) can block on long AI tasks — async/streaming required in new UI.
- Vector memory hybrid is lightweight; large corpora will need real embedding index.

---

## 10. Test coverage gaps

| Area | Status |
|------|--------|
| Cognitive unit/integration | Good |
| Security gate | Present |
| SelfView / SelfMutate | Present |
| FastAPI full contract | Thin |
| WebSocket events | Missing |
| Durable tasks | Missing |
| React/TS | N/A |
| Rust/Tauri | Minimal |
| E2E install→chat→shutdown | Missing |
| Windows packaging | Script-level only |

---

## 11. Deployment / packaging problems

- No single `Zenthon.exe` that starts Rust supervisor → Python backend → Ollama check → UI.
- User still expected to know `python run.py` / venv / ollama in many paths.
- NSIS exists but is not the target Tauri-based installer.
- `pyproject.toml` still describes classic ML platform (version 1.0.0, Production/Stable) — **misaligned** with honest v0.7 cognitive prototype README.

---

## 12. What stays in Python (cognitive layer)

- BrainOrchestrator, ReasoningEngine
- MemoryManager, CurriculumEngine
- AgentManager, Planner, Task Engine (logic)
- SelfView / SelfImprove / SelfMutate
- Knowledge (facts/graph), RAG pipeline logic
- FastAPI gateway
- Security gate / sandbox policy
- LLMProvider implementations

---

## 13. What moves to / is owned by Rust (system layer)

- Tauri shell + window lifecycle
- Process supervisor (Python API, Ollama, workers)
- Crash recovery, restart limits, backoff
- System tray, notifications
- Secure IPC boundary
- Resource monitoring hooks
- Application data path layout
- Startup sequence (runtime check → backend → health → UI)

**Rule:** Rust must not reimplement AI reasoning.

---

## 14. What moves to TypeScript / React (UI layer)

- Dashboard, Chat, Agents, Tasks, Memory, Knowledge, RAG, Self View, System, Diagnostics, Settings
- Streaming chat UI, Markdown, citations, evidence, agent status, task progress
- API client + WebSocket client generated from OpenAPI where practical
- No AI reasoning, no unrestricted FS, no shell from React

---

## 15. Migration risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| JSON → SQLite data loss | High | Dual-read migration; keep `data/leon/` intact until verified |
| Breaking single reasoning path | Critical | Never bypass Orchestrator/ReasoningEngine |
| Agent family unification regressions | Medium | Feature flags; keep react/coding production |
| Port binding change (0.0.0.0 → 127.0.0.1) | Low | Document LAN opt-in |
| Tauri packaging on Windows only | Medium | CI Windows job; keep Python fallback path |
| pyproject / requirements drift | Medium | Align versions and classifiers to reality |
| Experimental agents promoted too early | Medium | Explicit EXPERIMENTAL.md + flags |

---

## 16. Dependency graph (simplified)

```
interfaces (CLI/API/GUI)
    → core.bootstrap / core.config / core.logger
    → brain.orchestrator
        → brain.reasoning.engine
            → knowledge.registry (facts, graph)
            → memory.* / learning
            → curriculum
            → brain.llm.*  (→ to become LLMProvider)
        → agents.manager → tools.registry → security.gate → sandbox/audit
        → brain.planning
        → brain.self_*
    → data/leon/*

native_core (optional accelerator) ← Python adapter only

(future) Tauri/Rust  ──localhost──► FastAPI ──► same cognitive path
(future) React/TS    ──IPC/HTTP──► Tauri / FastAPI
```

---

## 17. Security boundaries (must remain)

```
User / Agent
  → Intent
  → Policy
  → Allowlist
  → Sandbox
  → Execute
  → Audit
```

- Default bind: **127.0.0.1**
- `LEON_ALLOW_MUTATE` default **false**
- No unrestricted FS/shell for agents
- No chain-of-thought dump to UI
- Security core / bootstrap / supervisor not mutable by SelfMutate

---

## 18. Recommended phase order (from spec, adjusted to reality)

| Phase | Focus | Notes |
|-------|-------|-------|
| **0** | This audit | Done |
| **1** | Architecture + domain contracts | Contracts for LLMProvider, Task, Event, Agent message |
| **2** | Python backend isolation | Clean public packages; no behavior change |
| **3** | FastAPI `/api/v1` gateway | health, chat, reason, agents, tasks, memory, knowledge, rag, models, system, self, tools |
| **4** | Event / WebSocket system | Typed events |
| **5** | Storage / SQLite migration | Keep JSON readable during transition |
| **6** | LLMProvider abstraction | OllamaProvider + MockProvider |
| **7** | AgentManager + Task Engine | Unify agents; durable tasks |
| **8** | RAG + memory modernization | Full local pipeline |
| **9** | React + TypeScript UI | Vite + Tailwind |
| **10** | Tauri + Rust runtime | Shell only |
| **11** | Process supervisor | Restart policy |
| **12** | Security hardening | Permissions model expansion |
| **13** | Self-view / improve integration in UI | |
| **14** | Windows packaging | Zenthon.exe + Setup |
| **15** | E2E tests | Install → chat → shutdown → restart |
| **16** | Documentation + final audit | Honest README |

**Hard rule:** Do not advance phase if tests fail.

---

## 19. What must not be done

1. Full rewrite from zero
2. Delete working ReasoningEngine / security gate / curriculum
3. Claim AGI or production-ready desktop before Definition of Done
4. Put AI logic in React or Rust
5. Default open network bind
6. Unrestricted self-mutation
7. Silent network failure presented as success
8. Empty skeletons marked production-ready

---

## 20. Immediate next actions (Phase 1)

1. Publish domain contracts (Python modules / Pydantic models):
   - `LLMProvider` interface
   - `Task` model + status enum
   - Typed `Event` model
   - Agent message / blackboard protocol
2. Align `pyproject.toml` metadata with honest v0.7 status (no false “Production/Stable”)
3. Document default bind `127.0.0.1` and port discovery strategy
4. Inventory all current FastAPI routes vs target `/api/v1/*`
5. Keep all existing cognitive tests green before any structural move

---

## 21. Definition of Done reference (target, not current)

See user specification §45. Current system satisfies the **cognitive Python core** subset and security gate. It does **not** yet satisfy Tauri shell, React UI, durable Task Engine, full RAG, process supervisor, or Windows installer as a single-click product.

---

*End of PHASE 0 audit. No production code changed in this phase.*
