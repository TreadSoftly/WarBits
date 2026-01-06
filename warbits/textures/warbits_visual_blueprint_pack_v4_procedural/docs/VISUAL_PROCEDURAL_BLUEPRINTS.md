# Procedural Blueprints Guide

You will never find perfect free blueprint/mesh data for *every* vehicle and weapon.
So we use a hybrid approach:

1) **Curated blueprints** (preferred)
   - Imported from meshes (OBJ) and converted to sparse wireframe edges.
   - Stored as JSONL for fast runtime load.

2) **Procedural blueprints** (fallback)
   - Generated from *dimensions* and a few behavioral tags.
   - Deterministic and LOD-friendly.
   - Looks consistent with your “tactical hologram” style.

This pack implements (2) cleanly and makes it easy to blend (1)+(2).

---
## What you got in this pack

- `warbits.visual.procedural.primitives`
  - box/cylinder/cone + merge utilities

- `warbits.visual.procedural.aircraft`
  - `JetParams`
  - `jet_params_from_spec(spec)`
  - `build_jet_blueprint(blueprint_id, params)`

- `warbits.visual.procedural.ground`
  - `TankParams`
  - `tank_params_from_spec(spec)`
  - `build_tank_blueprint(blueprint_id, params)`

- `warbits.visual.procedural.ordnance`
  - `MissileParams`, `RocketParams`, `BombParams`
  - `build_missile_blueprint`, `build_rocket_blueprint`, `build_bomb_blueprint`

- `warbits.visual.defaults`
  - `build_default_blueprint_db()` (registers canonical procedural prototypes)

- `warbits.visual.visual_resolver`
  - `VisualResolver`:
    - looks up by ID in DB
    - tries kind+tags match
    - otherwise generates and registers a procedural blueprint

---
## How to use it right now (Matplotlib)

1) Build a DB:

```python
from warbits.visual.defaults import build_default_blueprint_db
from warbits.visual.visual_resolver import VisualResolver

db = build_default_blueprint_db()
resolver = VisualResolver(db)
```

2) Resolve a spec dict:

```python
fake_fighter = {
    "name": "Fighter Test",
    "visual_kind": "aircraft",
    "length_m": 15.7,
    "wingspan_m": 10.6,
    "height_m": 4.8,
    "twin_tail": True,
}
bp = resolver.resolve("vehicle:test_fighter", fake_fighter)
```

3) Render bp with the Matplotlib blueprint layer you already have from v3.

---
## Notes on accuracy

These procedural generators are intentionally “low poly / 16-bit-ish”:
- They respect length/span/height proportions.
- They produce a stable silhouette that reads correctly at distance.
- They do **not** attempt exact panel lines or true geometry.

The plan is:
- Procedural first (coverage = 100%)
- Replace with curated mesh-derived blueprints when available (quality increases)
- Both render identically because they share the same Blueprint schema.
