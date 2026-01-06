# WarBits Visual System Tracker (Blueprints + Renderers)

This tracker is meant to be **boring and useful**.

- Each milestone is a deliverable that can be merged and tested.
- “Done” means: code exists, docs exist, and at least one test exists.

## Overall goal
Build a renderer-agnostic **Visual Blueprint DB** (wireframe geometry + anchors + LOD),
and then provide **two render backends**:

1. Matplotlib backend (debug/analysis/prototyping)
2. Panda3D backend (real-time, uncapped FPS)

## Milestones

### M0 — Visual Blueprint spec + research
Status: **DONE**
Deliverables:
- Blueprint schema (JSONL records)
- Extraction approach (mesh -> vertices/edges)
- LOD plan and “wireframe ribs” idea

### M1 — Ingest pipeline (mesh -> blueprint JSONL)
Status: **DONE**
Deliverables:
- Tools to load meshes (GLB/OBJ recommended)
- Wireframe extraction & simplification
- Writes blueprint JSONL

### M2 — Runtime (load DB, registry, LOD selection, transforms)
Status: **DONE**
Deliverables:
- BlueprintDB loader/validator
- BlueprintRegistry
- LODPolicy, Transform helpers

### M3 — Matplotlib renderer integration (this pack)
Status: **DONE**
Deliverables:
- `warbits.visual.mpl` package
- Batched `MPLBlueprintLayer` using `Line3DCollection`
- HUD helpers
- Tests in `tests/test_visual_mpl_blueprint_layer.py`

### M4 — Matplotlib post-FX: pixel mode + glow tuning
Status: **NEXT**
Deliverables:
- Pixel upscaler mode (render low-res then scale)
- Optional line dithering / “scanline” overlay
- Perf toggles (quality levels)

### M5 — Panda3D wireframe renderer (high FPS)
Status: **NEXT**
Deliverables:
- Panda3D `GeomLines`/`GeomLinestrips` renderer
- Batching by material + role
- Dynamic vertex buffer updates

### M6 — Panda3D post-FX: pixel scaling + bloom-ish glow
Status: **NEXT**
Deliverables:
- Render-to-texture, nearest-neighbor upscaling
- Minimal bloom pass (optional)
- Palette mapping + distance fade

### M7 — Auto-generated fallback blueprints from vehicle specs
Status: **NEXT**
Deliverables:
- If no mesh exists for a vehicle, build a parametric wireframe
  from dimensions (length / wingspan / turret ring / etc.)
- Stores result into the blueprint DB

### M8 — Asset catalog + alias mapping
Status: **NEXT**
Deliverables:
- Map War Thunder / your normalized vehicle ids -> blueprint ids
- Robust alias matching ("F-15C" == "F15" == "McDonnell Douglas F-15")

### M9 — Visual QA + performance bench
Status: **NEXT**
Deliverables:
- Snapshot renders for a curated set of vehicles/weapons
- Regression checks (edge counts, bounding boxes, anchor sanity)
- Simple FPS benchmark harness (Matplotlib + Panda3D)

## Current “definition of done” for visuals (v1)
Consider the visual system “v1 complete” when:
- M0..M6 are done (Matplotlib + Panda3D usable)
- M8 is done (catalog mapping)
- M9 is done (QA and perf baseline)

That is **7 milestones remaining after this pack** (M4..M9).
