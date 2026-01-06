# Visual System Tracker (Blueprint DB + Renderers)

Goal: **WarThunder-ish simulation overlay visuals** that are:
- accurate in silhouette (per vehicle / weapon)
- readable at game scale
- fast enough for uncapped FPS (budgets + batching + LOD)
- renderer-portable (Matplotlib now, Panda3D later)

---

## Status legend
- ✅ done
- 🟡 in progress / partial
- ⛔ not started

---

## Pack plan (v0 → v11)

### v0 — Research + Spec ✅
- Visual language spec (wireframe/hologram + 16-bit vibe)
- License notes + open-source leads
- DB schema concept + extraction strategy

### v1 — Ingest foundation ✅
- Base JSONL blueprint schema
- Minimal mesh ingestion hooks
- Early roundtrip tests

### v2 — Runtime core ✅
- Blueprint schema + DB loader
- Mesh IO + wireframe edge extraction
- LOD policy (`lod0/lod1/lod2/lod3`) + transforms
- CLI tools: build + preview

### v3 — Matplotlib style layer ✅
- Matplotlib wireframe style presets
- Fast(ish) 3D line layer (Line3DCollection)
- Deterministic “sim overlay” look

### v4 — Procedural blueprint library ✅
- Procedural primitives (box/wedge/cylinder/wing)
- Template builders: aircraft / ground / ordnance
- Registry + resolver defaults

### v5 — Panda3D renderer baseline ✅
- Panda3D line batching
- Blueprint rendering layer
- Minimal example app

### v6 — Panda3D terrain + HUD + pixel pass ✅
- Heightfield-ish terrain rendering
- HUD layer scaffolding
- Pixel/post-process pipeline hooks

### v7 — Tooling: atlas + metrics + budgets ✅ (this pack)
- Atlas generator (fast QA over hundreds of blueprints)
- Metrics report JSON (edges/verts/bounds)
- Budget validator (FPS guardrail)

### v8 — Data-driven mapping 🟡
- Map WarBits entity IDs → blueprint templates + parameters
- Use normalized data to scale templates (length/span/height)
- Coverage report: “what has a blueprint vs missing”

### v9 — Performance hardening ⛔
- Automatic LOD generation from a “lod0” blueprint
- Budget-aware edge decimation
- Batch renderers optimized for large entity counts

### v10 — Matplotlib “final form” ⛔
- Full overlay scene: terrain + entities + tracers + HUD
- Profiling hooks + replay capture
- Render determinism + golden-image tests

### v11 — Panda3D “final form” ⛔
- Instancing strategy + GPU-friendly line drawing
- Full HUD + target boxes + radar/SA page
- Replay/spectator camera modes

---

## Definition of Done (100%)

We are “done” when:

1) **Coverage:** 90%+ of in-sim entities resolve to a blueprint (vehicle/weapon/sensor/effect).  
2) **Readability:** `lod0/lod1/lod2` remain identifiable for silhouette + role.  
3) **Performance:** budgets enforced; no accidental 5,000-edge monsters.  
4) **Portability:** same blueprint DB renders in Matplotlib and Panda3D with minimal glue.  
5) **Tooling:** atlas + report used in CI/dev to prevent regressions.

---

## What you do right now (fast wins)

1) Put your current `blueprints.jsonl` in a stable spot, e.g. `data/visual/blueprints.jsonl`
2) Run:
   - `python -m warbits.visual.tools.pipeline atlas --db data/visual/blueprints.jsonl --out artifacts/atlas_iso.png --lod lod0`
   - `python -m warbits.visual.tools.pipeline report --db data/visual/blueprints.jsonl --out artifacts/blueprint_report.json --lod lod0`
   - `python -m warbits.visual.tools.pipeline validate --db data/visual/blueprints.jsonl --lod lod2`
3) Use the report to identify:
   - missing blueprint entries
   - edge-count offenders (budget failures)

That tells us exactly what the next iteration should target — no busywork.
