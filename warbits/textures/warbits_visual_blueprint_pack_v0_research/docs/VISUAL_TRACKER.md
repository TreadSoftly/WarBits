# Visual System Tracker (WarBits)

This tracker is scoped ONLY to visuals:
geometry blueprints + rendering style for Matplotlib and Panda3D.

-------------------------------------------------------------------------------
STATUS KEY
-------------------------------------------------------------------------------
- TODO: not started
- WIP: started but not validated
- DONE: implemented + tested + documented

-------------------------------------------------------------------------------
ITERATION PLAN (14 total)
-------------------------------------------------------------------------------

V0  Research + schema + skeleton (this pack)
- Deliverables:
  - VisualBlueprint schema + registry skeleton
  - OBJ loader + feature-edge extraction skeleton
  - Matplotlib wireframe rendering helpers (minimal)
  - docs: plan, sources, tracker
- DoD:
  - unit tests pass for schema + OBJ loader

V1  Blueprint DB “index + licenses” format + CLI tooling
- Add:
  - assets/visual/blueprints/blueprints.json format + loader
  - assets/visual/blueprints/licenses.json format + validator
  - CLI: `warbits tools visual-validate` and `warbits tools visual-list`
- DoD:
  - missing license entries are detected as errors

V2  Matplotlib style pack: holo wireframe (production-ready)
- Add:
  - glow multi-pass lines (silhouette + ribs)
  - dash patterns / depth cue rules
  - pixel-mode option (quantize line sampling)
  - terrain styles: wireframe grid, topo lines, rain overlay
- DoD:
  - stable FPS (no per-frame allocations that explode)

V3  Mesh import pipeline: OBJ → compiled wireframe (.npz) + LOD
- Add:
  - compile script `visual_compile_obj.py`
  - LOD tiers (near/med/far)
  - edge simplification + rib sampling
- DoD:
  - compiled cache loads and renders with Matplotlib

V4  FlightGear importer: AC3D (.ac) parsing → compiled wireframe
- Add:
  - `.ac` parser (minimal but robust)
  - FlightGear package discovery (walk directories)
  - per-aircraft scaling/orientation config
- DoD:
  - at least 3 aircraft imported end-to-end

V5  Weapon archetypes: missiles, bombs, rockets, guns
- Add:
  - parametric models (cylinder + fins, ogive noses, stabilizers)
  - scaling rules from warbits data (where present)
- DoD:
  - weapons look distinct and readable at distance

V6  Aircraft archetype library (fallback models)
- Add:
  - fighter/attacker/bomber archetypes
  - tail configs: single/twin/canted
  - engine count cues
- DoD:
  - “no mesh available” still produces a plausible silhouette

V7  Ground archetype library (fallback models)
- Add:
  - MBT / IFV / SPAA / SAM archetypes
  - turret + barrel + radar dish options
- DoD:
  - ground targets are clearly class-identifiable

V8  “Silhouette hull” pipeline (3‑view drawings → 3D wireframe)
- Add:
  - import 3-view silhouette images
  - voxel carving + marching cubes
  - compile to wireframe
- DoD:
  - 1 aircraft reconstructed from public blueprint drawings

V9  Runtime integration with WarBits (entity_id → blueprint)
- Add:
  - link VisualRegistry to DataStore
  - automatic scale from dimensions (when available)
  - graceful fallbacks + warnings
- DoD:
  - selecting any vehicle in data yields a renderable blueprint

V10 Panda3D renderer base: fast wireframe drawing
- Add:
  - batched line segments
  - per-frame transform updates without rebuild
- DoD:
  - stable high FPS with 1000s of segments

V11 Panda3D holo style: glow/pixel mode
- Add:
  - additive blending + shader line thickness
  - optional bloom pipeline
  - pixel mode (nearest filter + post quantization)
- DoD:
  - visual parity with Matplotlib style

V12 UI/HUD style pack (minimal but “War Thunder readable”)
- Add:
  - range rings, lead indicator, reticle, labels
  - optional sensor/radar overlay
- DoD:
  - UI is readable and does not tank FPS

V13 Asset build + packaging rules
- Add:
  - build scripts that generate compiled assets
  - manifest checksums
  - license export for distribution
- DoD:
  - clean-machine build produces same compiled assets deterministically
