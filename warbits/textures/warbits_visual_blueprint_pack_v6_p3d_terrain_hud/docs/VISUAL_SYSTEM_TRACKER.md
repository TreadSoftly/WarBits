# Visual System Tracker (Wireframe Blueprint DB)

This tracker is **for the VISUALS ONLY** (wireframe/pixel look + blueprint database + render layers).
It is intentionally separate from the physics/simlib tracker.

We are building a **single “visual truth” layer** that can feed:
- **Matplotlib** (debug + legacy viewport)
- **Panda3D** (future high-FPS viewport)

Core idea:
- **Simulation state** stays renderer-agnostic.
- **Visual blueprints** map `vehicle_id / weapon_id / sensor_id` → a *wireframe blueprint*.
- Blueprints can be sourced from:
  - mesh ingestion (.obj/.glb → edges)
  - procedural generators (fallback)
  - curated overrides (later)

---------------------------------------------------------------------------
## The 14-Pack Plan (v0 → v13)

We are intentionally shipping this as **14 incremental “packs”** so you can apply them safely.

### Completed packs
- **v0 — Research & Core Schema**
  - Vision docs + core terminology.
  - Minimal wireframe schema for “vertices + edges + metadata”.

- **v1 — Mesh Ingestion (OBJ/GLB)**
  - Import pipeline for `.obj` (always) and `.glb/.gltf` (optional dependency).
  - Wireframe edge extraction + decimation hooks.

- **v2 — Runtime Blueprint DB**
  - Blueprint DB read/write (JSONL) and fast lookup.
  - LOD selection (edge budget per distance).
  - Registry caching (avoid repeated parsing).

- **v3 — Matplotlib Visual Layer**
  - Neon wireframe style presets.
  - Matplotlib line rendering that is deterministic and LOD-aware.

- **v4 — Procedural Blueprints**
  - Procedural generators (air/ground/ordnance) as **fallback** when no mesh exists.
  - Consistent coordinate conventions + unit handling.

- **v5 — Panda3D Wireframe Layer (High-FPS path)**
  - Optional Panda3D renderer support (no hard dependency).
  - A dynamic, batched line renderer designed for “uncapped FPS”.

### This pack
- **v6 — Panda3D Terrain + Camera + HUD primitives**
  - Heightfield surface + sparse wire grid overlay (Matplotlib-ish terrain readability)
  - Chase camera controller (stable smoothing across uncapped FPS)
  - Basic HUD primitives (text blocks + center reticle)

### Remaining packs (planned)
- **v7 — Blueprint DB tooling: atlas/preview, batch build, perf reporting**
- **v8 — License/provenance metadata + filtering gates (ship-safe assets)**
- **v9 — Manual blueprint override system (patches, anchors, mountpoints)**
- **v10 — Effects visuals (tracers, explosions, trails) in the same style**
- **v11 — UI overlays (targets, lock rings, labels) cross-renderer**
- **v12 — Sprite baking (pixel-mode textures from wireframes)**
- **v13 — Full integration hooks into WarBits renderers + benchmark harness**

---------------------------------------------------------------------------
## Status

**Packs completed:** v0 → v6 (7/14)  
**Packs remaining:** v7 → v13 (7/14)

---------------------------------------------------------------------------
## “Definition of Done” for the visual system

We call the visual system “done” when:

1) Any entity with an ID can render *something* (mesh blueprint or procedural fallback).
2) The style is consistent:
   - silhouette edges are always readable
   - internal ribs are controlled and LOD-aware (no spaghetti)
3) Matplotlib mode is usable for debugging.
4) Panda3D mode is fast and stable (the “real viewport”).
5) The blueprint DB is auditable:
   - every blueprint has provenance metadata
   - license filters can exclude non-redistributable assets

