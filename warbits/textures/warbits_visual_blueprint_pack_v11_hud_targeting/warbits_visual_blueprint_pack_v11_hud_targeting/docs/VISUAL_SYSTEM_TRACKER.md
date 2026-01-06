# WarBits Visual Blueprint System — Tracker

This tracker is for the **visual subsystem** (wireframe vehicle/weapons/terrain + HUD) used by:
- Matplotlib renderer (debug/prototyping)
- Panda3D renderer (real-time)

The visual system is built in **packs** to keep integration controlled.

## Completed packs

- v0 (research): Visual blueprint DB goals, licensing & provenance notes.
- v1 (ingest): Non-Blender ingestion approach; OBJ-first; optional GLB/FBX.
- v2 (runtime): Blueprint schema, DB loader, registry; deterministic ID strategy.
- v3 (mpl): Matplotlib wireframe renderer building blocks (fast update patterns).
- v4 (procedural): Parametric blueprint generators for fallback coverage.
- v5 (panda3d): Panda3D renderer scaffold + wireframe style.
- v6 (p3d terrain + hud baseline): Terrain + HUD basics in Panda3D.
- v7 (tooling): CLI helpers (blueprint preview/build/export).
- v8 (mapping): Vehicle/weapon ID -> blueprint mapping policy.
- v9 (anchors + scale): Hardpoint anchors, uniform scaling, mount helpers.
- v10 (effects): Event-driven VFX blueprint + renderers (explosions, smoke, trails).

## v11 — HUD + Targeting (THIS PACK)

Status: **DONE**

Adds:
- Renderer-agnostic HUD primitives (`warbits.visual.hud.types`)
- Projectors (pinhole test projector) (`warbits.visual.hud.projector`)
- Target lead math (`warbits.visual.hud.targeting`)
- HUD builder that emits primitives (`warbits.visual.hud.builder`)
- Matplotlib HUD overlay renderer (`warbits.visual.mpl.hud_overlay`)
- Panda3D HUD overlay renderer (`warbits.visual.panda3d.hud_overlay`)

Done means:
- HUD primitives are stable and can be rendered without allocations each frame.
- Lead pipper + target box work deterministically.

## Remaining packs

### v12 — Performance harness + LOD policy

Status: PENDING

Will add:
- Frame-time budgets for visuals (per subsystem)
- LOD selection policy for blueprints (distance + screen size)
- Batch builders (minimize draw calls for many projectiles)
- Optional "pixel mode" post-pass for Panda3D (render-to-texture downscale)

### v13 — Data-driven accuracy expansion + packaging

Status: PENDING

Will add:
- Vehicle dimension inference from your normalized dataset (when available)
- Blueprint DB growth strategy: "generic fallback" -> "curated exact" pipeline
- Blueprint authoring helpers (semi-manual) with strict schema validation
- Packaging recommendations for shipping visual assets
