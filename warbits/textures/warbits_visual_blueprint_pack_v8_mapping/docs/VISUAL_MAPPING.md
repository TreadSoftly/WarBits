# Visual Mapping Guide

This guide explains how **WarBits IDs** (vehicles, weapons, etc.) turn into **visual blueprints**.

At runtime, the renderer should never guess. The mapping layer resolves:

`(entity_kind, entity_id, spec) -> VisualBinding -> Blueprint`

A `VisualBinding` answers:
- which blueprint to use (mesh-derived or procedural)
- which parameters to use (for procedural shapes)
- which style preset to use (holo green, team red, etc.)
- any LOD policy overrides

---

## The three layers of authority

1) **Manual overrides (you win)**
   - You can force an entity to use a specific blueprint or params.

2) **Mesh blueprints (if they exist)**
   - If your blueprint DB already contains a blueprint for this entity, use it.

3) **Procedural fallback**
   - If nothing else matches, we generate a clean, deterministic “generic” blueprint.

---

## The override file

Overrides are where you lock specific vehicles to specific meshes.

### JSON override format (recommended)

```json
{
  "vehicle": {
    "F-15C": {
      "blueprint_id": "mesh:vehicles_f15c",
      "scale": 1.0,
      "style": "holo_green"
    }
  },
  "weapon": {
    "AIM-9L": {
      "blueprint_id": "mesh:aim9l"
    }
  }
}
```

### JSONL override format

Each line is:

```json
{"entity_kind":"vehicle","entity_id":"F-15C","binding": {"blueprint_id":"mesh:vehicles_f15c"}}
```

---

## Suggestions mode

If you have a lot of ingested meshes, you don’t want to hand-map everything.

The `suggest` tool generates **candidate matches** using token overlap:

```bash
python -m warbits.visual.tools.pipeline suggest \
  --data-dir warbits/data \
  --blueprints warbits/visual/assets/blueprints.jsonl \
  --out warbits/visual/assets/visual_suggestions.jsonl
```

Then you copy the ones you accept into `visual_overrides.json`.

---

## Notes on naming

Matching improves massively if you adopt a consistent naming policy for blueprint IDs.

Good:
- `mesh:F15C`
- `mesh:t_80bvm`
- `mesh:aim_9l`

Bad:
- `mesh:scena_final2`
- `mesh:project`

Even if you don’t have the perfect database yet, clean naming makes everything easier.
