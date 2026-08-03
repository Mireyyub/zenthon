---
name: aurora-dev-cortex
description: Aurora Dev Cortex workflow for designing and implementing cognitive AI systems like Leon. Use when architecting thinking brains, memory tiers, curriculum learning, reasoning engines, agent tool loops, planners, or phase-based cognitive roadmaps. Triggers include cortex, cognitive architecture, ThinkingBrain, memory hierarchy, GraphRAG design, agentic loop.
---

# Aurora Dev Cortex

Design and implement **cognitive cores** (not chatbot wrappers). Optimized for Leon/zenthon-class systems.

## Cortex stack

```
Interfaces → Orchestrator → ReasoningEngine
  → Knowledge + Memory + LearningEngine
  → Agents/Tools (allowlist) + Planner
  → Persist data/<ai>/
```

## Design rules

1. Single reasoning path
2. Evidence first (curriculum/facts/graph before free LLM)
3. Conflict → UNKNOWN
4. Promote only validated learning records
5. Tools behind allowlist + path sandbox
6. Traces persist with trace_id
7. Claims = code
8. Legacy ML isolated from cognitive core

## Phase template

0 config/bootstrap → 1 persist → 2 curriculum → 3 reason → 4 memory → 5 agents → 6 planner → 7 interfaces → 8 tests → 9 security

## Anti-patterns

- Multiple competing brains
- LLM-only curriculum answers
- Shell tools without allowlist
- In-memory-only knowledge
- Dual APIs without deprecation
