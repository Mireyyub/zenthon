# ARCHITECTURE_AUDIT.md

**Repo:** Mireyyub/zenthon  
**Identity:** Leon  
**Declared version:** v0.8.0 Alpha (cognitive prototype + hybrid desktop path)  
**Audit dates:** 2026-08-28 (Phase 0) · **refresh after Phases 1–12**  
**Target:** Hybrid Local Multi-Language Production-Grade Desktop AI (Windows 11 first)  
**Rule:** Do not rewrite from scratch. Keep working cognitive core.

---

## 0. Executive summary (real state — post Phase 12)

| Layer | Reality now | Target (spec §45) | Gap |
|-------|-------------|-------------------|-----|
| Cognitive core | **Strong** ReasoningEngine, curriculum, memory, agents, planner, self_*, security | Keep Python brain | Low |
| FastAPI `/api/v1` | **Present** chat/think/reason/agents/tasks/memory/knowledge/self/models/tools/media/system | Full gateway | Medium (streaming, request IDs, RAG routes thin) |
| LLMProvider | **Present** OllamaProvider + Mock; wired into CoT/ToT/SoT/RAG/agents | Full abstraction | Low |
| Events / WS | **Present** typed EventName + `/ws` | Rich agent progress stream | Medium |
| SQLite | **Partial** tasks durable; facts/graph still JSON-primary | Full SQLAlchemy categories | Medium–High |
| React UI | **Seed client** `ui/` chat+status (no Tailwind full app) | Full dashboard suite | High |
| Tauri / Rust shell | **Seed only** `desktop/tauri` + native_core helpers | Real window + sidecar | High |
| Process supervisor | **Python** `core/supervisor.py` working; not Rust-owned | Rust supervisor | Medium |
| Packaging | **PyInstaller + NSIS scripts** | Single-click Tauri product | Medium–High |
| RAG | **Basic** chunk/retrieve/persist + optional generate | Parser→rerank full pipeline | High |
| Multi-agent | react/coding prod; local_agi/crew experimental | Unified blackboard cycle | Medium |
| Security | Gate + sandbox + allowlist + audit | Expanded permission model | Medium |
| E2E | **API smoke** + manual Windows checklist | Install→signed product E2E | Medium |
| Offline-first | Mostly yes; soft LLM failure | Explicit OFFLINE everywhere | Low–Medium |

**Honest one-liner:** Leon is a **real offline-first cognitive prototype** with hybrid *path* (API, provider, UI seed, supervisor, packaging scripts). It is **not** yet the full Definition of Done desktop product (Tauri shell, full React suite, full RAG, signed installer).

**Do not start over.** Continue from gaps below.

---

## 1. What was completed (Phase 0–12 mapping)

| Spec phase (original) | Our execution | Status |
|----------------------|---------------|--------|
| 0 Audit | `ARCHITECTURE_AUDIT.md` | Done (+ this refresh) |
| 1 Domain contracts | `core/contracts/*`, LLMProvider | Done |
| 2 Public surface | `docs/PUBLIC_SURFACE.md`, deprecation, 127.0.0.1 | Done |
| 3 FastAPI v1 | `interfaces/api/v1/*` | Done (expand remaining) |
| 4 Events/WS | typed bus + `/ws` | Done (enrich payloads) |
| 5 SQLite | tasks + migrate helpers; facts/graph JSON dual-read | Partial |
| 6 LLMProvider | wired reasoning + agents + embed path | Done |
| 7 Agents/tasks | agents on provider; TaskStore SQLite | Partial vs full AgentManager blackboard |
| 8 RAG/memory | disk RAG index; not full document pipeline | Partial |
| 9 React UI | `ui/` Vite React chat+status | Partial (not full screens) |
| 10 Tauri+supervisor | Python supervisor + Tauri **seed** | Partial |
| 11–14 Packaging / security / self UI | packaging scripts; security exists; UI self thin | Partial |
| 15 E2E | `e2e_desktop_smoke.py` + checklist | Partial |
| 16 Docs | PUBLIC_SURFACE, DESKTOP, PACKAGING, E2E | Ongoing |

---

## 2. KEEP (do not delete)

- `brain/orchestrator.py`, `brain/reasoning/engine.py` — single public path  
- `knowledge/registry`, FactStore, Graph, LearningEngine  
- `curriculum/`, evaluation  
- `security/gate.py`, sandbox, allowlist, audit  
- Production agents: `react`, `coding`  
- `brain/planning`, self_view / self_improve / gated self_mutate  
- `interfaces/api/main.py` + `/api/v1`  
- `brain/llm/provider.py`  
- `core/supervisor.py`  
- Tests under `tests/unit` + cognitive integration  

---

## 3. LEGACY (isolate, migrate later)

See `LEGACY.md`: `models/`, `training/`, Flask `interfaces/web`, classic inference demos, Tkinter as *long-term* UI (still functional today).

---

## 4. Definition of Done — honest checklist

| Item | State |
|------|--------|
| Windows 11 desktop application | Partial (PyInstaller path / scripts) |
| Tauri shell | Seed only |
| React/TypeScript UI | Minimal client |
| Rust runtime | Seed + native_core helpers |
| Python cognitive core | **Yes** |
| FastAPI local gateway | **Yes** |
| WebSocket events | Yes (basic) |
| Local Ollama integration | **Yes** |
| LLM provider abstraction | **Yes** |
| SQLite persistence | Partial (tasks; not all domains) |
| Memory / Knowledge graph | **Yes** |
| Full RAG pipeline | Partial |
| Multi-agent system | Partial (prod pair + experimental) |
| Durable task engine | Partial |
| Planner / coding / research | Yes (research thinner) |
| Critic / Executor | local_agi present; not fully unified |
| Security gate + sandbox | **Yes** |
| SelfView / SelfImprove / SelfMutate | **Yes** (gated) |
| Audit logs | **Yes** |
| Offline mode | Mostly |
| Process supervision | Python yes; Rust no |
| Crash recovery | Basic backoff |
| Windows installer | Scripts; not store-grade |
| Uninstaller | NSIS section |
| Migration JSON→SQLite | Helpers; facts/graph still JSON |
| Unit / integration / E2E | Good cognitive; E2E API-level |
| CI/CD | `ci_eval.sh` + unit; TS/Rust CI weak |
| Documentation | Improving; README still slightly stale |

---

## 5. Priority backlog (no rewrite)

### P0 — truth & safety
1. Align README: default bind **127.0.0.1**, remove forced autostart claims, document Phase 9–12 paths.  
2. Security permissions expansion (FS/shell/network classes) without bypassing gate.  
3. Never claim production desktop until Tauri+installer verified on Windows hardware.

### P1 — product path
4. React UI expansion: Dashboard, Tasks, Memory, Knowledge (still API-only).  
5. Real Tauri app scaffolding with sidecar → `python -m core.supervisor`.  
6. RAG: document parsers (md/txt/pdf/json) + metadata + retriever API route.  
7. Facts/graph dual-write SQLite when ready (non-destructive).

### P2 — depth
8. Unified AgentManager + blackboard in cognitive cycle.  
9. Chat streaming + request_id on API.  
10. Resource monitor hooks (psutil) on `/api/v1/system`.  
11. Port discovery (preferred → free port → UI config).  
12. TS/Rust CI jobs when toolchain available.

---

## 6. Language boundaries (unchanged)

| Language | Owns |
|----------|------|
| **Python** | Cognitive brain, FastAPI, agents, RAG logic, security policy |
| **Rust** | Desktop lifecycle, process supervisor (target), IPC, tray — **no AI** |
| **TypeScript/React** | UI only — **no reasoning, no shell, no unrestricted FS** |

---

## 7. Security boundaries (must remain)

```
User/Agent → Intent → Policy → Allowlist → Sandbox → Execute → Audit
```

- Default bind `127.0.0.1`  
- `LEON_ALLOW_MUTATE=false`  
- No CoT dump to UI  
- Security/bootstrap/supervisor not mutable by SelfMutate  

---

## 8. Dependency graph (current)

```
ui/ (React) ──HTTP──► FastAPI /api/v1 ──► BrainOrchestrator
                              │
                              ▼
                     ReasoningEngine
                              │
              curriculum / facts / graph / memory / LLMProvider
                              │
                     agents + security.gate
                              │
                        data/leon/*

core.supervisor ──spawns──► uvicorn (Python)
desktop/tauri   ──seed──► (future webview + sidecar)
leon_desktop.py ──► supervisor + Tkinter
```

---

## 9. Immediate next work (recommended)

**Not** “Phase 0 again.” Next productive slice:

1. **Docs honesty pass** (README + default bind).  
2. **Security hardening** (`security/permissions.py` expansion + tests).  
3. **RAG v2** (ingest files → index → `/api/v1/rag/*`).  
4. **UI expansion** (dashboard panels on existing API).  
5. **Tauri real wire** only when Windows + toolchain available for verification.

---

## 10. What must not be done

1. Full rewrite  
2. Delete ReasoningEngine / security gate / curriculum  
3. Fake AGI / production claims  
4. AI logic in React or Rust  
5. Default open network bind  
6. Unrestricted self-mutation  
7. Silent network success  
8. Empty skeleton = “done”  

---

*Refresh after hybrid Phases 1–12. Cognitive core remains the asset. Gaps are desktop productization, full RAG, and real Tauri — not absence of a brain.*
