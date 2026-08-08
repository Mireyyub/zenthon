# Leon Architecture (canonical)

Identity: **Leon** · Repo: Mireyyub/zenthon · Status: v0.7 cognitive prototype

## Single cognitive path

```
CLI / GUI / FastAPI (interfaces.*)
        ↓
BrainOrchestrator.run()
        ↓
ReasoningEngine.reason()     ← only public think path
        ↓
Curriculum → Facts → Graph → Memory → (optional) LLM backend
        ↓
Agents (react, coding) | Planner | Security gate
        ↓
data/leon/{facts,graph,learning,memory,traces,plans,audit,sandbox,mutations,self_improve,self_view,system}
```

## Self layers (introspection + evolution)

```
SelfView          → see organs/cells, lines, AST, search
SelfImproveEngine → diagnose → teach/learn → verify (multi-round)
SelfMutateEngine  → allowlisted source/curriculum mutation + backup/rollback
CodeAuthor        → write new helpers under CREATE_PREFIXES
code_verify       → green-gate (compile/import/call/smoke)
SystemLoop        → whole-system status + improve orchestration
mutate_allowlist  → shared write policy (security/core/kernel forbidden)
```

## Public API surface

| Use | Module |
|-----|--------|
| Think / reason | `brain.reasoning.engine.ReasoningEngine` or `BrainOrchestrator.run` |
| Teach | `curriculum.CurriculumEngine` |
| Memory | `memory.MemoryManager` / `memory.retrieve` |
| Facts / Graph | `knowledge.registry.get_fact_store` / `get_graph` |
| Agents | `agents.manager.agent_manager` (prod: react, coding) |
| Security | `security.gate.safe_tool_call` |
| Start | `core.bootstrap.start_leon` |
| Body map | `brain.self_view.SelfView` |
| Improve | `brain.self_improve.improve_auto` |
| System | `brain.system_loop.SystemLoop` |

## Not public (internal / legacy)

| Path | Role |
|------|------|
| `brain.core_brain.ThinkingBrain` | LLM reasoning backend only |
| `brain.core.Brain` | Thin legacy stub |
| `models/`, `training/`, `inference/predictors` | LEGACY ML demos — see LEGACY.md |
| `interfaces/web` | Legacy Flask UI |
| `inference/api/fastapi_app` | Deprecated re-export of `interfaces.api.main` |

## Design rules

1. One reasoning path — no parallel ad-hoc answerers for user queries
2. Evidence before free LLM
3. Conflict → UNKNOWN
4. Promote only validated learning records
5. Tools behind allowlist + path sandbox
6. Source mutation: allowlist + `LEON_ALLOW_MUTATE` + green-gate + backup
7. Claims in README = code behavior
