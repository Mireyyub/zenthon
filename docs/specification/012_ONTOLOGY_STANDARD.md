# Ontology Standard

## Purpose
Defines how LEON represents concepts.

## Top Classes
- Entity
- Concept
- Event
- Process
- Attribute
- Relation

## Entity Rules
- Immutable ID
- Human-readable name
- Optional aliases
- Typed attributes
- Version history

## Relation Types
- is_a
- instance_of
- part_of
- contains
- causes
- depends_on
- before
- after
- located_in

## Validation
- No circular `is_a`
- All relations reference valid IDs
