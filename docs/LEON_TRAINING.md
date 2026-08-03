# LEON Training Specifications

**Source:** Google Drive folder `Leon.təlim` (Sprints 01–09)

## Layout

| Path | Content |
|------|--------|
| `docs/specification/` | Standards **001–023** |
| `genome/` | Cognitive genes (Existence, Object, …) |
| `schemas/` | JSON schemas (node, event, plan, learning) |
| `datasets/foundation.jsonl` | Foundation Q/A seed |
| `examples/` | Plan examples |
| `training/tests/` | Validation / learning engine cases |
| `curriculum/volumes/01_foundation/` | Genesis Curriculum Volume 01 |

## Sprints map

| Sprint | Content |
|--------|--------|
| 01 | Learning / Dataset / Memory standards |
| 02 | Reasoning, KG, Decision, Confidence |
| 03 | Memory layers + genome + foundation dataset |
| 04 | Ontology, Entity, Property, Relation models |
| 05 | Event, Context, Trace, Validation |
| 06 | Reasoning Engine specification |
| 07 | Knowledge Graph Engine specification |
| 08 | Learning Engine specification |
| 09 | Planner Engine specification |

## Use

```bash
# Curriculum (Volume 01 Foundation)
python -m interfaces.cli.main_cli teach-volume 01

# Specs guide implementation of brain/, knowledge/, memory/, learning/
```

Integrated into [Mireyyub/zenthon](https://github.com/Mireyyub/zenthon).
