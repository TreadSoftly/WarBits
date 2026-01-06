# Visual Blueprint System Tracker (v0 → v13)

This tracker is the canonical "where we are" for the Visual Blueprint system.

## Definition of "baseline complete"
Baseline complete means:
- One Visual Blueprint DB (JSONL) feeds both renderers (Matplotlib + Panda3D).
- VisualMap resolves every known entity_id to a visual binding.
- Procedural fallback ensures 100% coverage even when meshes are missing.
- QA and perf regression tools exist and can run headless.

## Status
- v0 Research + schema: DONE
- v1 Ingest (OBJ/GLB) → blueprint JSONL: DONE
- v2 Runtime DB + registry + LOD plumbing: DONE
- v3 Matplotlib batch renderer: DONE
- v4 Procedural fallback blueprints: DONE
- v5 Panda3D wireframe batch renderer: DONE
- v6 Panda3D terrain/camera/HUD primitives: DONE
- v7 Tooling (atlas, budgets, metrics): DONE
- v8 Mapping (entity_id → blueprint/proc fallback): DONE
- v9 Anchors + attachments + scale-fit: DONE
- v10 FX (tracers/trails/explosions/impacts): DONE
- v11 HUD targeting + overlays: DONE
- v12 Perf harness + deterministic LOD + batching primitives: DONE
- v13 Consolidation + QA gates + coverage + provenance + perf regression: DONE (this pack)

## Verification checklist (do these before wiring into the sim)
1) Build/refresh the blueprint DB:
   - python -m warbits.visual.tools.build_blueprints --in assets/models_raw --out data/visual/blueprints.jsonl

2) Build anchors:
   - python -m warbits.visual.tools.anchors_cli build --blueprints data/visual/blueprints.jsonl --anchors-out data/visual/anchors.jsonl

3) Build or refresh VisualMap:
   - python -m warbits.visual.tools.pipeline map --data-dir warbits/data --blueprints data/visual/blueprints.jsonl --out data/visual/visual_map.json

4) Run QA validate:
   - python -m warbits.visual.tools.pipeline validate

5) Run coverage:
   - python -m warbits.visual.tools.pipeline coverage

6) Run provenance strict check (only if you are shipping):
   - python -m warbits.visual.tools.pipeline provenance --strict

7) Run perf regression harness:
   - python -m warbits.visual.tools.pipeline perfreg

Artifacts are written into ./artifacts.
