---
name: perfect-code
description: High-quality code craft for Python projects like Leon/zenthon. Use when writing, reviewing, or refactoring production-grade Python modules, tests, CLI/API surfaces, persistence, security gates, and clean architecture. Triggers include perfect code, refactor, code quality, clean architecture, solid Python, review this module.
---

# Perfect Code

Raise code to clear, testable, honest, safe quality.

## Non-negotiables

1. One responsibility per module
2. Explicit types + dataclasses where fit
3. Honest errors (no silent swallow on critical paths)
4. No fake success — stub/offline modes explicit
5. Tests for persist round-trip and path escape
6. Secrets only via env
7. Minimal public API
8. Docs match behavior

## Prefer

- pathlib Path + resolve for sandbox
- centralized write_json/read_json
- soft optional imports with status flags
- structured results (ok/data/error)

## Security

Allowlist tools, path sandbox for writes, audit gated calls.

## Refactor order

correct → explicit failures → types → tests → dedupe → docs
