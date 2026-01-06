# Matplotlib Blueprint Renderer Guide (WarBits)

This guide assumes:
- You have a Visual Blueprint JSONL file (built from meshes OR parametric generator).
- Your sim has entities with position + orientation + blueprint_id.

## 1) Put the code where Python can import it

Copy the folder:

- `warbits/visual/`

into your repo at:

- `warbits/visual/`

(not inside `warbits/lib/...`)

Your imports should work as:

```python
from warbits.visual.blueprint_db import BlueprintDB
from warbits.visual.registry import BlueprintRegistry
from warbits.visual.mpl.blueprint_layer import MPLBlueprintLayer, BlueprintInstance
```

## 2) Load the blueprint DB once at startup

Example:

```python
from warbits.visual.blueprint_db import BlueprintDB
from warbits.visual.registry import BlueprintRegistry

BLUEPRINT_DB_PATH = "warbits/data/normalized/visual_blueprints.jsonl"

db = BlueprintDB.load_jsonl(BLUEPRINT_DB_PATH)
registry = BlueprintRegistry(db)
```

Keep `registry` somewhere global-ish (renderer init) so you do NOT reload the JSONL per frame.

## 3) Create the MPLBlueprintLayer inside your Matplotlib renderer

Example:

```python
import matplotlib.pyplot as plt
from warbits.visual.mpl.style import apply_mpl_dark_theme, neon_green_style
from warbits.visual.mpl.blueprint_layer import MPLBlueprintLayer

fig = plt.figure(figsize=(10, 7))
ax = fig.add_subplot(111, projection="3d")
apply_mpl_dark_theme(fig, ax)

layer = MPLBlueprintLayer(ax, registry, style=neon_green_style(), enable_detail=True)
```

## 4) Each sim frame: build instances and call layer.update()

Map your sim entities to blueprint instances. You need:
- blueprint_id (string)
- position (x,y,z) in meters
- rotation matrix (3x3) OR identity

Example:

```python
from warbits.visual.mpl.blueprint_layer import BlueprintInstance

instances = []
for ent in sim.entities:
    instances.append(
        BlueprintInstance(
            blueprint_id=ent.blueprint_id,
            position_m=(ent.pos.x, ent.pos.y, ent.pos.z),
            rotation_mat=ent.R_world_from_body,  # 3x3
            scale=1.0,
            role=("friendly" if ent.team == 0 else "hostile"),
        )
    )

layer.update(instances, camera_pos=(cam.x, cam.y, cam.z))
```

## 5) Performance notes (Matplotlib)

Matplotlib 3D is not a game engine.

This layer does the main things that matter:
- **Batches** units into 1 Line3DCollection per role + pass
- Avoids creating artists per unit

If you still need more FPS:
- Disable detail: `enable_detail=False`
- Disable glow: `style = neon_green_style(); style = style.__class__(...)` (or edit style defaults)
- Reduce edges during blueprint build (max_edges, fewer ribs)

## 6) Preview tool

If you have a JSONL blueprint DB, you can preview any model with:

```bash
python -m warbits.visual.tools.mpl_preview --db path/to/visual_blueprints.jsonl --id your_blueprint_id
```

Save a PNG:

```bash
python -m warbits.visual.tools.mpl_preview --db path/to/visual_blueprints.jsonl --id your_blueprint_id --save out.png
```
