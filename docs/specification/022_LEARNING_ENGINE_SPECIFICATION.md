# 022 Learning Engine Specification

## Purpose
Convert validated observations into durable knowledge.

## Pipeline
Observe -> Normalize -> Parse -> Compare -> Validate -> Learn -> Index

## Learning Sources
- User interaction
- Documents
- Tool outputs
- Knowledge graph

## Rules
- Unverified facts are quarantined.
- Existing knowledge is never silently overwritten.
- Every learned item stores provenance.

## Memory Promotion
Working -> Episodic -> Semantic

## Output
- Knowledge update proposal
- Confidence
- Learning trace
