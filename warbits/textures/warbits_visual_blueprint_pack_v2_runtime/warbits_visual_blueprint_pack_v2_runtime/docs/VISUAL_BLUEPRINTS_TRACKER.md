# Warbits Visual Blueprints Tracker

This tracker is **only** for the *visual blueprint* pipeline: making accurate, high-FPS, see-through wireframe depictions
for **all** vehicles/weapons/entities, driven by IDs (vehicle_id / weapon_id / etc).

Design goals (non-negotiable)
- **FPS first:** heavy geometry work happens offline at build-time. Runtime only loads compact blueprint data + applies transforms.
- **Renderer-agnostic:** same blueprint DB should feed both Matplotlib and Panda3D renderers.
- **Data-driven IDs:** visuals are looked up by canonical IDs (vehicle_id / weapon_id / warhead_id / sensor_id).
- **Coverage-aware:** we always know what IDs lack a blueprint and which fallback was used.

What "done" means for the baseline (v0 -> v4)
- A single JSONL blueprint DB format exists and is stable.
- Tools exist to ingest:
  - 3D meshes (OBJ/GLB) -> wireframe edges (+ LODs)
  - optional 2D line drawings (SVG) -> 2D outline blueprints (future pack)
- Runtime registry loads DB(s), resolves IDs, selects LOD, and provides geometry quickly.
- Matplotlib renderer can draw blueprints with the chosen "holographic wireframe" style.
- Panda3D renderer can draw the same blueprints at high FPS with batching/instancing.

-------------------------------------------------------------------------------

## Milestones

### M0 — Research + constraints (DONE in v0)
- Licensing/provenance checklist
- Candidate free sources (Wikimedia SVG line drawings, OpenVSP, etc.)
- DB format sketch + ingestion plan

Status: DONE (visual_blueprint_pack_v0_research)

### M1 — Mesh ingestion toolchain (DONE in v1)
- Load mesh assets (OBJ/GLB) via trimesh
- Extract feature edges (crease/boundary) with deterministic sampling
- Build JSONL blueprint DB
- Preview tool (Matplotlib) for quick inspection

Status: DONE (visual_blueprint_pack_v1_ingest)

### M2 — Runtime registry + LODs + normalization hooks (THIS PACK: v2)
Deliverables:
- Stable schema supports:
  - wire3d blueprint (vertices + edges)
  - optional LOD edge sets (lod0/lod1/lod2...)
  - meta for scale/orientation
- Runtime registry:
  - load N JSONL DB files
  - resolve best blueprint for an ID
  - select LOD based on distance policy
- LOD edge extraction upgrade:
  - generate multiple LOD edge sets at build-time
  - optional "rib" line generation knobs (build-time only)
- Unit tests for schema, lod logic, registry loading

Status: DONE (visual_blueprint_pack_v2_runtime)

### M3 — Matplotlib integration pack (NEXT)
Deliverables:
- WireframeArtistCache:
  - prebuild edge segments
  - in-place updates only (no remove/re-add)
  - optional cheap glow pass (off by default)
- Update MatplotlibRenderer to draw blueprints for:
  - aircraft
  - ground units
  - missiles/rockets/bombs (blueprint or procedural fallback)
- Performance knobs:
  - per-entity LOD thresholds
  - max wire segments per frame budget
  - fallback to marker-only LOD for very far entities

Status: PENDING

### M4 — Panda3D wireframe integration pack (NEXT+1)
Deliverables:
- Blueprint -> Panda3D Geom (static) builder
- Instance caching (one Geom per blueprint, many NodePaths)
- Dynamic line batches for high-count objects (bullets/tracers)
- Pixel-perfect post pipeline (optional):
  - render to low-res buffer
  - nearest-neighbor upsample
  - optional bloom/glow

Status: PENDING

### M5 — SVG blueprint ingestion (OPTIONAL but high-coverage)
Deliverables:
- Ingest Wikimedia SVG line drawings into Outline2D blueprints
- Runtime can render outline2d as billboarded wireframe
- Coverage improves massively without needing 3D meshes for everything

Status: PENDING

-------------------------------------------------------------------------------

## Current recommended execution order (to stay sane)
1) Build blueprints from your current assets -> generate a DB JSONL.
2) Use the preview tool to verify orientation/scale visually.
3) Integrate registry into MatplotlibRenderer (M3).
4) Integrate registry into Panda3DRenderer (M4).
5) Expand coverage by adding assets + (optional) SVG ingestion (M5).

-------------------------------------------------------------------------------

## Performance rules (practical)
- **No per-frame allocations** in the render hot path if avoidable.
- Cache:
  - blueprint lookup results
  - per-blueprint local segments
  - renderer-specific geometry objects
- LOD must be enforced. Unlimited detail == guaranteed stutter.
