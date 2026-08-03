# 023 Planner Engine Specification

## Purpose
Transform a goal into an executable plan.

## Inputs
- Goal
- Constraints
- Available tools
- Current context
- Memory

## Planning Cycle
1. Define goal
2. Decompose into tasks
3. Resolve dependencies
4. Estimate cost/risk
5. Prioritize
6. Produce execution graph
7. Monitor progress
8. Replan if needed

## Task States
pending
ready
running
blocked
completed
failed
cancelled

## Replanning Triggers
- New information
- Failed task
- Constraint change
- User intervention
