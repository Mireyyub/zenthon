# 021_KNOWLEDGE_GRAPH_ENGINE_SPECIFICATION
Version: 1.0.0

## Objective
The Knowledge Graph (KG) is LEON's canonical semantic store.

## Node Types
- Entity
- Concept
- Event
- Rule
- Procedure

## Edge Types
- is_a
- instance_of
- part_of
- has_property
- causes
- depends_on
- before
- after
- related_to

## Node Requirements
- Immutable id
- Type
- Name
- Description
- Language
- Version
- Confidence
- Source references
- Attributes
- Relations

## Graph Operations
create_node()
update_node()
merge_node()
delete_node()
link_nodes()
unlink_nodes()
query()

## Merge Policy
Nodes may merge only when:
- same identity
- no conflicting immutable fields
- provenance preserved

## Query Stages
1. Parse
2. Candidate retrieval
3. Graph traversal
4. Ranking
5. Validation
6. Return

## Integrity Rules
- No orphan relations.
- No circular is_a chains.
- Every relation references existing nodes.
