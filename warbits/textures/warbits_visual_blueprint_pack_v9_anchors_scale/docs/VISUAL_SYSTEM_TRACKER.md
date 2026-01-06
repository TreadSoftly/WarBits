# Visual Blueprint System Tracker (v0 → v13)

Goal: **War Thunder-ish visual fidelity** with **wireframe / holo / 16-bit overlay aesthetics**, driven by your *real sim data*, while staying compatible with:

- **Matplotlib renderer** (prototyping, offline renders, dataset generation, debug/replay)
- **Panda3D renderer** (real-time, high-FPS gameplay)

This tracker is organized by “packs” because that matches how you’ve been building the repo.

---

## Status

### Completed packs (v0 → v9)

- [x] **v0 – Research baseline**
  - Visual language, style constraints, core coordinate conventions.
- [x] **v1 – Ingest**
  - Load mesh formats (OBJ/GLB/etc where supported), normalize, split into parts.
- [x] **v2 – Runtime**
  - Blueprint DB, registry cache, transforms, LOD policy.
- [x] **v3 – Matplotlib**
  - Wireframe terrain, blueprint layer, camera setup, HUD skeleton.
- [x] **v4 – Procedural**
  - Parametric fallback blueprints (aircraft/ground/ordnance primitives).
- [x] **v5 – Panda3D**
  - Wireframe line batching + pixel pipeline (engine-facing baseline).
- [x] **v6 – Panda3D terrain + HUD**
  - Terrain grid/heightfield hook points, 2D overlay entry points.
- [x] **v7 – Tooling**
  - CLI pipeline, reporting, preview hooks.
- [x] **v8 – Mapping**
  - Resolve sim entities → blueprint IDs (aliases, rules, fallbacks).
- [x] **v9 – Anchors + Attachments + Scale Fit**
  - Anchor DB (JSONL), default anchor generation, mount weapons, scale-fit helpers.

---

## Remaining packs (v10 → v13)

These are the final 4 packs that bring the visual system from “baseline works” to “this is a real engine subsystem”.

### v10 – Effects library (tracers / contrails / explosions / impacts)
- [ ] Tracer rendering: bullets, shells, autocannon streams (batched)
- [ ] Contrails / smoke trails: cheap spline-ish polyline with LOD
- [ ] Explosion primitives: wireframe shock sphere + fragment burst lines (fast, deterministic)
- [ ] Impact decals (wireframe splats) as optional “aesthetic mode”
- [ ] Matplotlib + Panda3D parity for core effects

### v11 – HUD / Symbology (War Thunder-ish)
- [ ] Flight HUD: speed/alt/heading, pitch ladder, velocity vector
- [ ] Target boxes + lead indicators + lock status
- [ ] Sensors overlay hooks (radar/TGP style)
- [ ] Replay overlay hooks (telemetry v7 pack, timeline scrubbing)

### v12 – Performance hardening (FPS-first)
- [ ] Segment builder + pooling (minimize allocations, fast updates)
- [ ] Distance + screen-space LOD (reduce internal ribs at range)
- [ ] Culling (distance + optional frustum)
- [ ] Panda3D instancing strategy for repeated blueprints
- [ ] “Budget governor” (cap segments per frame; degrade gracefully)

### v13 – Data-driven accuracy + packaging
- [ ] Read real dimensions from your normalized War Thunder datasets (length/span/height)
- [ ] Auto-scale-fit based on those dims per vehicle/weapon
- [ ] “Visual Blueprint DB” format finalization (schema + versioning)
- [ ] License/provenance manifest for any third‑party reference assets
- [ ] Golden render tests (render → hash/metrics) for regression detection

---

## Definition of “done”

The visual system is considered complete when:

1) Given an entity ID (vehicle/weapon), the system can always:
   - resolve it to a blueprint (mesh-derived OR procedural fallback)
   - scale it to plausible real dimensions (if dims exist)
   - attach loadout items to anchors (if applicable)

2) The same blueprint + mapping can be rendered in:
   - Matplotlib (debug/replay/exports)
   - Panda3D (real-time)

3) Performance knobs exist to keep you above your FPS target:
   - LOD
   - culling
   - batching
   - segment budgets
