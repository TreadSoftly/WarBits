# Visual Blueprints Runtime (v2)

This pack adds the *runtime* pieces needed to use visual blueprints in renderers.

What you get
- `warbits.visual.Blueprint` schema:
  - supports wire3d with optional LOD edge sets
  - forward-compatible for future outline2d (SVG ingestion)
- `warbits.visual.BlueprintDB`:
  - loads JSONL and indexes by blueprint_id
- `warbits.visual.VisualRegistry`:
  - caches numpy arrays for fast renderer use
  - selects LOD deterministically via `LODPolicy`
- Updated ingestion tools:
  - `python -m warbits.visual.tools.build_blueprints ...` builds LOD edge sets
  - `python -m warbits.visual.tools.preview_wireframe ...` previews a blueprint

Why this matters for FPS
- The registry converts Python lists/tuples into **numpy arrays once**.
- Renderers can then build segments using vectorized indexing (`verts[edges]`) and only update transforms.
- LOD selection is per-entity and deterministic.

Where this plugs in next
- MatplotlibRenderer: use `VisualRegistry.geometry()` + `edges_for_distance()`
- Panda3D: build one `Geom` per blueprint (LOD0) and instance it, plus swap LOD geoms by distance.

Quick commands
- Build:
  - `python -m warbits.visual.tools.build_blueprints --assets assets --out data/visual_blueprints.jsonl --preset balanced`
- Preview:
  - `python -m warbits.visual.tools.preview_wireframe --db data/visual_blueprints.jsonl --id <some_id> --lod lod0`
