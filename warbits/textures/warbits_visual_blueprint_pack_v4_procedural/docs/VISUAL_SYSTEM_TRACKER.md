# Visual System Tracker (Blueprint DB + Renderers)

This tracker is the *single source of truth* for the visual stack work.
The goal is to make **every vehicle + weapon + effect** renderable in a consistent,
War-Thunder-ish tactical wireframe style — first in Matplotlib (debug/replay),
then in Panda3D (real FPS).

---
## Milestones

### M0 — Style language + constraints (DONE)
- Establish the wireframe look: silhouette edges + sparse ribs + canopy/intakes hints
- Define palettes (phosphor green baseline), LOD targets, and perf goals

### M1 — Blueprint schema + JSONL format (DONE)
- Blueprint object: vertices_m + edges + lod_edges + tags + meta
- Deterministic serialization (json lines)

### M2 — Blueprint DB + registry (DONE)
- In-memory DB with tag-based selection and compatibility checks

### M3 — Mesh ingest (OBJ -> wireframe edges) (DONE)
- Minimal OBJ ingest pipeline (no Blender required)
- Wireframe extraction with edge filtering + optional LOD

### M4 — Runtime hooks + ID mapping scaffolding (DONE)
- Runtime mapping stubs (vehicle_id -> blueprint_id)
- Placeholders for future: caching, streaming, per-scenario overrides

### M5 — Matplotlib blueprint renderer layer (DONE)
- Render Blueprints as Line3DCollection batches
- LOD policy hooks
- HUD stubs

### M6 — Matplotlib terrain base layer (DONE)
- Terrain wireframe/grid helpers
- Camera defaults for “tactical replay” vibe

### M7 — Procedural primitives + auto-blueprints (DONE in v4)
- Procedural generators:
  - aircraft (jet-like)
  - ground (tank-like)
  - ordnance (missile/rocket/bomb)
- VisualResolver: DB first, then procedural fallback
- DimensionResolver: robust schema-tolerant dimension extraction

### M8 — Matplotlib VFX pack (NEXT)
- Glow (double-pass lines) + phosphor flicker (seeded/deterministic)
- Damage state cues: jitter, missing segments, intermittent dropout
- Weapon tracers and explosion rings as wireframe primitives

### M9 — Matplotlib performance pack (NEXT)
- Segment batching + cache-friendly transforms
- View-frustum culling + distance-based LOD selection
- Profile harness: count segments, frame time, update budgets

### M10 — Panda3D renderer skeleton (UPCOMING)
- Optional dependency (imports must not break if Panda3D isn’t installed)
- Window + camera + scenegraph + basic controls
- Load Blueprint edges and draw them

### M11 — Panda3D wireframe “neon hologram” look (UPCOMING)
- Line rendering strategy:
  - GeomLinestrips for thin lines
  - Billboarded quads for thick lines (GPU-friendly)
- Postprocess glow (Render-to-texture) in pixel mode

### M12 — Asset build pipeline (UPCOMING)
- Convert any input mesh (OBJ/GLB/FBX via external converter) -> Blueprint JSONL
- Pack blueprints with versioning (manifest + hashes)
- Regression tests: visual/edge-count stability

### M13 — Content coverage pass (UPCOMING)
- Ensure every known vehicle + weapon resolves to a blueprint:
  - exact blueprint
  - or procedural fallback with dimensions
- Add a “coverage report” that flags missing/unknown kinds

---
## Definition of Done (v1 of visuals)
- You can select *any* vehicle or weapon ID from your normalized dataset and:
  - it resolves to a Blueprint (exact or procedural)
  - renders in Matplotlib in the right style
  - has LOD edges (silhouette/low) for performance
- Panda3D renderer loads the same Blueprint DB and displays the same assets.
