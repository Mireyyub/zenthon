# Leon Architecture (canonical)

**Identity:** Leon · **Repo:** Mireyyub/zenthon · **Status:** v0.8.0 Alpha cognitive prototype (+ hybrid desktop path)

See also: [`ARCHITECTURE_AUDIT.md`](ARCHITECTURE_AUDIT.md) · [`docs/GAP_ANALYSIS.md`](docs/GAP_ANALYSIS.md) · [`docs/PUBLIC_SURFACE.md`](docs/PUBLIC_SURFACE.md)

## Single cognitive path

```
CLI / GUI / FastAPI / React ui
        ↓
BrainOrchestrator.run()
        ↓
ReasoningEngine.reason()     ← only public think path
        ↓
Curriculum → Facts → Graph → Memory → LLMProvider (optional)
        ↓
Agents (react, coding) | Planner | Security gate
        ↓
data/leon/{facts,graph,learning,memory,traces,plans,audit,sandbox,mutations,...}
```

## Hybrid layers (honest)

| Layer | Reality |
|-------|--------|
| Python cognitive core | Primary, mature |
| FastAPI `/api/v1` | Local gateway; default **127.0.0.1** |
| React `ui/` | Minimal chat/status client — no AI in browser |
| Process supervisor | Python `core/supervisor.py` |
| Tauri / Rust | Seed only — no AI in Rust |
| Packaging | PyInstaller/NSIS scripts — not store-grade |

## Self layers

```
SelfView          → organs/cells, AST, search (restricted FS)
SelfImproveEngine → diagnose → teach/learn → verify
SelfMutateEngine  → allowlist + LEON_ALLOW_MUTATE + backup/rollback
SystemLoop        → status + improve orchestration
```

## Public API surface (Python)

| Use | Module |
|-----|--------|
| Think / reason | `BrainOrchestrator` / `ReasoningEngine` |
| LLM | `brain.llm.get_llm_provider` |
| Teach | `curriculum.CurriculumEngine` |
| Memory | `memory.retrieve` / `MemoryManager` |
| Facts / Graph | `knowledge.registry` |
| Agents | `agents.manager.agent_manager` |
| Security | `security.gate.safe_tool_call` |
| Start | `core.bootstrap.start_leon` |
| Desktop readiness | `native_core.desktop_status` |
| Supervisor | `core.supervisor` |

## Design rules

1. One reasoning path — no parallel ad-hoc answerers for user queries  
2. Evidence before free LLM; conflict → UNKNOWN  
3. Promote only validated learning records  
4. Tools behind allowlist + path sandbox  
5. Source mutation gated; security/bootstrap not mutable  
6. Default network bind **127.0.0.1**  
7. Claims in README = code behavior  
8. No AI logic in React or Rust  

## Not public

| Path | Role |
|------|------|
| `brain.core_brain.ThinkingBrain` | Internal LLM backend |
| `models/`, `training/`, classic inference | LEGACY — see LEGACY.md |
| `interfaces/web` | Legacy Flask |
