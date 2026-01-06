# Visual Blueprint Pipeline (VBD)

This module set is for converting *source 3D meshes* (OBJ/GLB, etc.) into a **Visual Blueprint Database**:
a lightweight, renderer-agnostic representation of each asset as **vertices + edges** (wireframe), plus
metadata needed to match WarBits `vehicle_id` / `weapon_id`.

Why do this?
- You can keep the sim authoritative and deterministic.
- You can render the same blueprint in Matplotlib now and Panda3D later.
- You can keep a consistent "War Thunder sim-replay hologram" aesthetic across everything.

## What this pipeline produces

A blueprint record (one per asset) containing:
- `blueprint_id`: stable identifier you choose (ex: `vehicle:t90a`, `weapon:aim9m`)
- `kind`: `vehicle` | `weapon` | `sensor` | `effect` | `terrain_prop`
- `vertices_m`: list of (x,y,z) floats in **meters**, in canonical axes (X forward, Y left, Z up)
- `edges`: list of (i,j) index pairs into `vertices_m`
- `tags`: style tags (ex: `tank`, `fighter`, `missile`, `rotary`)
- `meta`: freeform metadata (license, source url, author, scale/orientation notes)

Recommended output layout:
- `assets/blueprints/blueprints.jsonl`  (one JSON per line)
- `assets/blueprints/README.md`         (provenance + rules)
- `assets/source_models/<asset_id>/...` (original mesh + license file)

## Accepted source formats

**Best choices to download** (lowest friction):
1) `*.obj`  (simple, readable, easiest to split by object name)
2) `*.glb` / `*.gltf`  (modern, good for Panda3D, but you need a loader; we use optional `trimesh`)
3) `*.fbx` / `*.blend` (fine as *source*, but you must export to OBJ/GLB for this pipeline)
4) `*.usdc` / USD       (skip unless you intentionally commit to a USD pipeline)

## Blender export rules (so assets ingest cleanly)

In Blender:
- Apply transforms: `Ctrl+A -> All Transforms`
- Set units: Metric, scale = 1.0
- Forward axis: X forward (or note your export so we can remap)
- Up axis: Z up
- Triangulate mesh (modifier or export option)
- Prefer **one vehicle per file** (or clean object names inside the file)

Export:
- For wireframe extraction: OBJ is perfect.
- For Panda3D runtime mesh rendering: GLB is ideal.

## Wireframe extraction policy (how we decide which edges to draw)

We want "see-through but readable":
- Always include boundary edges.
- Include *feature edges* where the dihedral angle is sharp (crease threshold).
- Optionally include a small % of extra edges ("ribs") for structural detail.
- Then apply a decimation pass to keep edge count bounded.

All of that is view-independent (no silhouette detection), so it works for Matplotlib and is deterministic.

## Next integration steps (not implemented in this pack)

1) Create `warbits/visual/blueprints/map.py`:
   - map `vehicle_id` -> `blueprint_id`
   - fallback to procedural blueprint if missing

2) Update renderers:
   - MatplotlibRenderer: draw blueprints as Line3DCollection
   - Panda3DRenderer: draw blueprints via LineSegs/GeomLines (batched)

3) Add "pixel mode":
   - render to low-res buffer, scale up with nearest-neighbor.

