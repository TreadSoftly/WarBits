# Visual Blueprint System Tracker

This tracker is **only** for the “visual blueprint” track:
- **Goal:** turn *any* vehicle/weapon/sensor in your data into a fast, readable, deterministic **wireframe/pixel-holo** representation.
- **Constraint:** simulation core stays the authority. Visuals consume state.
- **Performance target:** visuals must have clear budgets (edges, draw calls, per-frame updates) so we don’t slowly build a 12 FPS haunted house.

---

## Definition of done (for this track)

We can call the visual system “baseline complete” when:

1) We can **render any entity** (vehicles + ordnance at minimum) in **Matplotlib** with:
   - silhouette-only LOD at distance
   - stable, readable holo-wireframe style
   - zero per-frame object creation in hot paths (update-in-place)

2) We can render the same entities in **Panda3D** with:
   - shared geometry per blueprint
   - per-entity transform updates only
   - optional HUD overlay

3) We have tooling to:
   - ingest meshes to blueprints
   - preview/atlas
   - generate reports + budget checks
   - build a VisualMap (IDs → visual binding)

---

## Pack history (what exists so far)

### v0 — Research pack ✅
- Terminology + design language for the wireframe/pixel-holo look
- Budget framing: edges per entity, per frame allocations, LOD needs

### v1 — Ingest pack ✅
- Mesh ingestion -> blueprint JSONL builder
- Supports safe formats first (.obj/.glb), with clear error handling

### v2 — Runtime concepts ✅
- Runtime “how to use blueprints in a loop” skeleton
- Early cache/LOD direction

### v3 — Matplotlib integration ✅
- Matplotlib preview renderer for blueprints
- Core blueprint DB schema + readers/writers

### v4 — Procedural library ✅
- Procedural blueprints for:
  - aircraft (generic fighter-ish)
  - tanks (generic MBT-ish)
  - ordnance (missile/rocket/bomb)
- Deterministic parameterization

### v5 — Panda3D baseline ✅
- Panda3D wireframe line batching primitives
- Node/geometry helpers that can be driven by blueprint edges

### v6 — Panda3D terrain + HUD ✅
- Heightfield terrain rendering helpers
- HUD overlay building blocks (screen-space)

### v7 — Tooling ✅
- Visual budget system + metrics
- pipeline CLI with:
  - atlas
  - report
  - validate

### v8 — Data-driven mapping ✅ (this pack)
- VisualMap builder (entity_kind/entity_id → VisualBinding)
- Resolver rules:
  - mesh blueprint if exists
  - otherwise procedural fallback
- Manual overrides loader (JSON/JSONL)
- Fuzzy matching suggestions tool (IDs ↔ blueprint IDs)
- pipeline CLI extended:
  - map
  - suggest

---

## Remaining packs (what’s left)

### v9 — Performance hardening 🟡
- “No surprises” perf rules enforced by tests:
  - update-in-place only
  - one allocation-free transform path
  - LOD thresholds + edge budgets
- More procedural families (AAA/SAM/trucks/ships) so coverage improves
- Optional additional mesh format support (trimesh/assimp path) behind guards

### v10 — Matplotlib “final form” 🟡
- Batch rendering:
  - one Line3DCollection per layer (silhouette/structure/detail)
  - per-frame numpy segment updates
- 2D overlay HUD with optional blit (where possible)
- Style presets: “War Thunder holo wireframe” + “pixel holo”

### v11 — Panda3D “final form” 🟡
- Shared geometry + instancing patterns
- Thick line option (billboarded quads) if needed
- Optional glow/bloom pipeline (cheap, controllable)
- Pixel mode textures + nearest filtering

---

## What you do right now

### 1) Generate mapping suggestions

This helps connect your ingested blueprint IDs to your WarBits entity IDs.

```bash
python -m warbits.visual.tools.pipeline suggest \
  --data-dir warbits/data \
  --blueprints warbits/visual/assets/blueprints.jsonl \
  --out warbits/visual/assets/visual_suggestions.jsonl
```

Review `visual_suggestions.jsonl` and create/extend an overrides file.

### 2) Create / update manual overrides

Example override file (JSON):

```json
{
  "vehicle": {
    "F-15C": {"blueprint_id": "mesh:vehicles_f15c"},
    "T-80BVM": {"blueprint_id": "proc:tank", "params": {"turret_ratio": 0.45}}
  },
  "weapon": {
    "AIM-9L": {"blueprint_id": "mesh:aim9l"}
  }
}
```

### 3) Build the VisualMap

```bash
python -m warbits.visual.tools.pipeline map \
  --data-dir warbits/data \
  --blueprints warbits/visual/assets/blueprints.jsonl \
  --overrides warbits/visual/assets/visual_overrides.json \
  --out warbits/visual/assets/visual_map.json
```

---

## Notes

- This visual track is deliberately **not** tied to a single renderer.
- The VisualMap is the “contract” that makes it possible to swap Matplotlib → Panda3D later without rewriting everything.
