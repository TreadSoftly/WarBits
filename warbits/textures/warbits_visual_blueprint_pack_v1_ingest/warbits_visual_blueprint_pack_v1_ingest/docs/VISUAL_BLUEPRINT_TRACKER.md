# Visual Blueprint DB Tracker

This tracker is *only* for visuals / blueprint DB work.
Keep it separate from sim/physics tracker so we don't mix goals.

## Current Status

- [x] VBD-0: Baseline schema + OBJ loader + wireframe extraction (research pack)
- [ ] VBD-1: Multi-object OBJ loader + optional GLB loader
- [ ] VBD-2: Blueprint DB writer/reader (JSONL) + provenance metadata
- [ ] VBD-3: Batch blueprint build tool (folder -> blueprints.jsonl)
- [ ] VBD-4: Matplotlib previewer (grid terrain + neon wireframe)
- [ ] VBD-5: Panda3D previewer (LineSegs) + pixel-mode render target
- [ ] VBD-6: Vehicle/weapon blueprint mapping to `vehicle_id` / `weapon_id`
- [ ] VBD-7: Procedural fallback generators (tank/fighter/missile/bomb)
- [ ] VBD-8: CI tests (schema validation + determinism + perf tripwires)

## "Done" definition for VBD baseline

Baseline is "done" when:
1) You can ingest OBJ/GLB assets and build `blueprints.jsonl`
2) You can preview any blueprint in Matplotlib without a running sim
3) A sample blueprint can render in Panda3D without hitching
4) You can map at least 10 real `vehicle_id`s to blueprints
5) Tests pass for loaders and extraction (deterministic output)

## What we should NOT do yet

- Fancy shading / textures / lighting.
- Full silhouette-edge extraction per frame (too expensive for MPL, unnecessary now).
- Spending time on perfect per-vehicle details before the pipeline is proven.

