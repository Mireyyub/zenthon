# Omniverse bridge detail

Package: integrations/omniverse/

## Status fields

- connected, pxr, omni_kit, objects, mode (live|stub)

## Workflow

1. status()
2. load_stub_demo_scene() OR sync_from_stage()
3. inject_scene_facts() optional
4. ask_leon(question) -> ReasoningEngine with scene context

## Live Kit notes

Requires omni.usd context and active stage. Outside Kit, always use stub.

## Security

No arbitrary filesystem from Omniverse bridge. Facts only via FactStore API.
