# Visual System Tracker (Blueprints + Renderers + FX)

This tracker is your **single source of truth** for the “wireframe War Thunder replay” visual system.

Rule: **finish the current pack before starting the next**.

---

## Status overview

- ✅ v0 Research + glossary + source list
- ✅ v1 Blueprint ingestion scaffolding (OBJ/GLB/FBX parsing paths)
- ✅ v2 Runtime blueprint DB + caching
- ✅ v3 Matplotlib renderer baseline (blueprints + terrain + HUD)
- ✅ v4 Procedural blueprint templates
- ✅ v5 Panda3D renderer baseline (blueprints)
- ✅ v6 Panda3D terrain + HUD baseline
- ✅ v7 Tooling (inspect, validate, export)
- ✅ v8 Mapping (data IDs → blueprint IDs)
- ✅ v9 Anchors + scale fitting
- ✅ v10 FX (tracers, trails, explosions, impacts)  ← **this pack**
- ⏳ v11 HUD + targeting suite (radar/IRST/lock cues, labels, lead indicator)
- ⏳ v12 Performance harness + LOD policy (stress tests, profiler hooks)
- ⏳ v13 Data-driven accuracy expansion + packaging (more blueprints, CI checks)

---

## What “done” means (per pack)

A pack is done when:

- It ships as a zip with:
  - docs explaining integration
  - tests proving the core math/logic
  - code that does not require you to guess how to wire it
- The pack adds **one coherent capability** (not random loose files).

---

## Pack v10 deliverables (FX)

✅ Implemented:

- `warbits.visual.effects` (renderer-agnostic FX generation)
  - pooled explosions + impact bursts
  - trail ring buffers for tracers and contrails
  - `FxManager` that merges layers into one frame batch
- Matplotlib adapter: `warbits.visual.mpl.effects_layer.MplFxLayer`
- Panda3D adapter: `warbits.visual.panda3d.effects_layer.P3DFxLayer`
- Unit tests for trail, explosion, burst, and manager logic

Key performance property: **hard caps** on total segments + pooled instances.

---

## Remaining work (next packs)

### v11 HUD + Targeting
- Target boxes (staple corners) that scale with range
- LOS / lock indicators (RWR-like alerts)
- Lead indicator for guns
- Missile seeker cone / acquisition box
- Optional “sim replay” annotations

### v12 Performance harness + LOD policy
- Headless benchmark script (spawn N aircraft + M tracers + terrain)
- LOD policy (drop detail edges + reduce trail history with distance)
- Profile report output compatible with `profiling/*.jsonl`

### v13 Data-driven accuracy expansion + packaging
- Expand blueprint set using:
  - procedural templates + scale anchors
  - imported models (when available)
- CI guardrails:
  - blueprint validation
  - renderer smoke tests
  - perf sanity checks

