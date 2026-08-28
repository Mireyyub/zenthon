# Gap analysis — Spec Definition of Done vs Leon v0.8

**Date:** 2026-08-28  
**Source of truth:** code + `ARCHITECTURE_AUDIT.md` (refreshed)

## Summary

| Category | Coverage |
|----------|----------|
| Cognitive Python core | ~85–90% |
| Local API gateway | ~75% |
| Security baseline | ~70% |
| Hybrid desktop product | ~25–35% |
| Full RAG | ~30% |
| Multi-agent unified | ~50% |
| Storage SQL-complete | ~40% |

## Recommended execution order (forward)

| Wave | Focus | Why |
|------|--------|-----|
| A | README honesty + security permissions | Trust + P0 |
| B | RAG ingest API + document types | Spec §18 |
| C | React dashboard pages (API-only) | Spec §27 without fake shell |
| D | Tauri real sidecar on Windows | Spec §10–12 |
| E | Facts/graph SQLite dual-write | Spec §24 |
| F | Streaming chat + request_id | Spec §26 |
| G | CI TS/Rust when toolchains exist | Spec §40 |

## Explicit non-goals this quarter

- Claiming AGI  
- Cloud-required features  
- Microservice mesh  
- Unrestricted agent shell  
