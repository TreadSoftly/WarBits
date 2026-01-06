# Visual Anchors, Attachments, and Scale Fit

This pack adds **three missing “glue layers”** that make visuals feel *War Thunder-ish* instead of “floating wireframe noodles”:

1) **Anchors** (named points on a blueprint: `nose`, `pylon_left_1`, `turret_pivot`, etc.)
2) **Attachments** (mount missiles/bombs/turrets at anchors)
3) **Scale Fit** (match a blueprint’s size to real-world dimensions when you have them)

The goal is to let your sim choose **ANY vehicle/weapon** and still render:
- the vehicle at the right physical scale
- weapons mounted in sensible places
- with deterministic, testable behavior

---

## What’s new

### `warbits.visual.anchors`
- `compute_default_anchors(...)` generates a baseline anchor set from the blueprint bounds.
- `AnchorDB` stores hand-authored overrides in **JSONL**.
- Defaults + overrides are merged, so you only manually edit what needs fidelity.

### `warbits.visual.scale_fit`
- `compute_uniform_scale(vertices_m, TargetDims(...))` returns a robust scalar scale.
- `compute_nonuniform_scale(...)` gives per-axis scale when you *must* stretch a placeholder.
- Intended use:
  - **accurate mesh-derived blueprints** → uniform scale
  - **procedural fallback shapes** → non-uniform scale (optional)

### `warbits.visual.attach`
- Minimal `Pose` + `AttachmentSpec`
- `attach_child_pose(...)` returns a child pose for a mounted weapon (inherits parent rotation by default)

### `warbits.visual.registry`
- Now optionally merges anchors via an `AnchorDB`
- Exposes cached bounds/center/dims for cheap scale-fit or culling decisions

---

## Recommended file layout in your repo

You can keep these in your existing visual data folder.

Example:

- `data/visual/blueprints.jsonl`
- `data/visual/anchors.jsonl`

(Names are up to you — the code just wants paths.)

---

## Tooling: build and edit anchors

### 1) Auto-generate anchors for everything

```bash
python -m warbits.visual.tools.anchors_cli build \
  --blueprints data/visual/blueprints.jsonl \
  --anchors-out data/visual/anchors.jsonl
```

### 2) Show anchors for one blueprint

```bash
python -m warbits.visual.tools.anchors_cli show \
  --blueprints data/visual/blueprints.jsonl \
  --anchors data/visual/anchors.jsonl \
  mesh:military_vehicles:Cube.005
```

### 3) Override/add an anchor

```bash
python -m warbits.visual.tools.anchors_cli set \
  --anchors data/visual/anchors.jsonl \
  mesh:military_vehicles:Cube.005 \
  pylon_left_1 "2.1, 3.8, -0.2"
```

### 4) Delete an anchor

```bash
python -m warbits.visual.tools.anchors_cli delete \
  --anchors data/visual/anchors.jsonl \
  mesh:military_vehicles:Cube.005 \
  pylon_left_1
```

---

## Using anchors + attachments at runtime

This is the “mount missiles under wings” baseline.

```python
import numpy as np

from warbits.visual.registry import VisualRegistry
from warbits.visual.attach import Pose, AttachmentSpec, attach_child_pose

reg = VisualRegistry.from_files(
    "data/visual/blueprints.jsonl",
    anchors_jsonl_path="data/visual/anchors.jsonl",
)

# Parent (aircraft)
parent_id = "aircraft:f16"
parent_pose = Pose(pos_m=np.array([0.0, 0.0, 1000.0]), rot=np.eye(3))
parent_scale = 1.0

anchors = reg.get_anchors(parent_id)

# Child (missile)
spec = AttachmentSpec(
    child_blueprint_id="weapon:aim9",
    parent_anchor="pylon_left_1",
    offset_local_m=np.array([0.0, 0.0, -0.15]),
)

child_pose = attach_child_pose(
    parent_pose=parent_pose,
    parent_scale=parent_scale,
    anchors=anchors,
    spec=spec,
)

# Now render parent + child as separate instances in your renderer layer.
```

---

## Scale-fit example

```python
from warbits.visual.scale_fit import TargetDims, compute_uniform_scale

V, E = reg.get_geometry("aircraft:f16", distance_m=2000.0)

# Suppose your data says the aircraft is ~15m long and 10m span:
dims = TargetDims(length_m=15.0, span_m=10.0)

scale = compute_uniform_scale(V, dims)
```

---

## Why this matters for FPS and “quality”

- **Anchors** remove expensive “guesswork” at runtime. You can compute once, cache forever.
- **Attachments** avoid per-frame procedural geometry. Just transform child instances.
- **Scale-fit** makes *every* vehicle look physically plausible, even if its blueprint is a fallback.

This lets you keep the visual system deterministic and cheap, while still looking intentional.
