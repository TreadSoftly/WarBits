# Visual Blueprint System v13 — Wiring Guide (Codex-first)

This doc assumes you already merged visual packs v0–v12 into the repo, and now you are merging v13.

Goal: make the visuals system *coherent* and *enforceable*:
- Every entity ID resolves to a visual (mesh blueprint or procedural fallback).
- Performance budgets and LOD rules are checked early (build-time and CI), not discovered during gameplay.
- Provenance/license metadata exists for anything that came from an external asset.

This guide is written to be handed to GPT-5.2 Codex inside VSCode.

---

## 0) Canonical folder conventions (do this once and stop debating paths)

Create these directories (repo root):

- `assets/models_raw/`
  - Raw downloads only. Do not edit these files. Prefer `.glb` and `.obj`.

- `data/visual/`
  - Runtime DB outputs (things your sim loads fast).

- `artifacts/`
  - Throwaway outputs: atlases, reports, perf logs.

Expected runtime DB files:

- `data/visual/blueprints.jsonl`
  - Wireframe blueprint DB (vertices + edges + lod_edges).

- `data/visual/anchors.jsonl`
  - Anchor points per blueprint for attachments (pylons, turret pivots, etc.).

- `data/visual/visual_overrides.json`
  - Your authoritative mapping corrections.

- `data/visual/visual_map.json`
  - Auto-built mapping from entity IDs → blueprints/procedural templates.

- `data/visual/provenance.jsonl`
  - License/source manifest per mesh blueprint.

---

## 1) Build pipeline — the exact order (don’t scramble it)

### Step 1.1 — Build blueprint DB from raw models

Use your existing builder tool (from earlier packs). Typical command looks like:

- `python -m warbits.visual.tools.build_blueprints --in assets/models_raw --out data/visual/blueprints.jsonl --preset balanced`

If your builder uses different flags, keep the *outputs* the same.

Definition of Done:
- `data/visual/blueprints.jsonl` exists and contains at least 1 record.

### Step 1.2 — Generate anchors (autobuild)

If you have the anchors CLI from v9:

- `python -m warbits.visual.tools.anchors_cli build --blueprints data/visual/blueprints.jsonl --anchors-out data/visual/anchors.jsonl`

Definition of Done:
- `data/visual/anchors.jsonl` exists.

### Step 1.3 — Build the VisualMap

Use your v8 mapping pipeline (or tool):

- `python -m warbits.visual.tools.pipeline map --data-dir warbits/data --blueprints data/visual/blueprints.jsonl --overrides data/visual/visual_overrides.json --out data/visual/visual_map.json`

If you do not have `map` in pipeline yet, use `build_visual_map.py` from v8.

Definition of Done:
- `data/visual/visual_map.json` exists.

### Step 1.4 — Run v13 QA (validate + coverage + provenance + perfreg)

This pack adds the v13 QA pipeline commands:

- Validate schema/anchors/budgets/scale:
  - `python -m warbits.visual.tools.pipeline validate --strict`

- Coverage report (every ID must resolve):
  - `python -m warbits.visual.tools.pipeline coverage --strict`

- Provenance/license check (strict mode recommended before shipping):
  - `python -m warbits.visual.tools.pipeline provenance --strict`

- Perf regression harness (deterministic, headless):
  - `python -m warbits.visual.tools.pipeline perfreg --frames 120 --seed 7`

Outputs:
- `artifacts/validate_report.json`
- `artifacts/visual_coverage_report.json`
- `artifacts/visual_missing_ids.jsonl`
- `artifacts/provenance_report.json`
- `artifacts/perf_report.json`

---

## 2) Runtime wiring — how the sim chooses visuals every frame

The runtime flow is:

1. Load `BlueprintDB` / `VisualRegistry` once at startup.
2. Load `anchors.jsonl` (if present) and merge into registry.
3. Load `visual_map.json` and `visual_overrides.json` (if used).
4. For each sim entity:
   - Resolve `entity_id → binding` using VisualMap/Resolver.
   - Binding yields either a `blueprint_id` or a procedural template.
   - Create a renderer instance with pose (pos + rotation + scale).
5. Renderer draws instances using batched layers.

### 2.1 — Where to wire it in WarBits

In your repo you likely have:
- `warbits/core/sim.py` (headless sim core)
- `warbits/rendering/matplotlib_renderer.py` (Matplotlib adapter)
- `warbits/rendering/panda3d_renderer.py` (optional)

The correct architecture:
- Simulation updates state.
- Renderer reads state and draws.
- Visual system sits inside renderer as a *view model*.

### 2.2 — Minimum integration for Matplotlib renderer

In `warbits/rendering/matplotlib_renderer.py`:

Startup (one-time):

```python
from warbits.visual.blueprint_db import BlueprintDB
from warbits.visual.registry import VisualRegistry

# Optional: VisualMap/Resolver (v8)
from warbits.visual.mapping.types import VisualMap
from warbits.visual.mapping.rules import resolve_visual_binding

# Matplotlib layers (v3/v10/v11)
from warbits.visual.mpl.blueprint_layer import MPLBlueprintLayer, BlueprintInstance
from warbits.visual.mpl.effects_layer import MplFxLayer
from warbits.visual.mpl.hud_overlay import MPLHudOverlay

# Load DBs
bp_db = BlueprintDB.load_jsonl("data/visual/blueprints.jsonl")
reg = VisualRegistry(bp_db)

# Optional anchors merge
anchors_path = "data/visual/anchors.jsonl"
if Path(anchors_path).exists():
    reg.load_anchors_jsonl(anchors_path)

# Load map (optional)
visual_map = None
vm_path = Path("data/visual/visual_map.json")
if vm_path.exists():
    visual_map = VisualMap.load(vm_path)

# Create layers
bp_layer = MPLBlueprintLayer(ax, reg, style=..., enable_detail=True)
fx_layer = MplFxLayer(ax)
hud_layer = MPLHudOverlay(fig, ax)
```

Each frame:

```python
instances = []
for ent in sim_state.entities:
    binding = resolve_visual_binding(
        entity_kind=ent.kind,
        entity_id=ent.entity_id,
        spec=ent.spec_dict,
        visual_map=visual_map,
        registry=reg,
    )

    instances.append(
        BlueprintInstance(
            blueprint_id=binding.blueprint_id,
            position_m=(ent.pos_x, ent.pos_y, ent.pos_z),
            rotation_mat=ent.R_world_from_body,
            scale=binding.scale,
            role=("friendly" if ent.team == 0 else "hostile"),
        )
    )

bp_layer.update(instances, camera_pos=(cam.x, cam.y, cam.z))

# FX + HUD update hooks (if you already wired v10/v11)
fx_layer.update(fx_frame_data)
hud_layer.update(hud_primitives)
```

Key performance rule:
- Create artists once, update data arrays only.

### 2.3 — Minimum integration for Panda3D renderer

Same flow, but use Panda3D layers:

```python
from warbits.visual.panda3d.blueprint_layer import BlueprintP3DLayer
from warbits.visual.panda3d.effects_layer import P3DFxLayer
from warbits.visual.panda3d.hud_overlay import P3DHudOverlay

bp_layer = BlueprintP3DLayer(parent_np=render, registry=reg, ...)
fx_layer = P3DFxLayer(parent_np=render)
hud_layer = P3DHudOverlay(parent=aspect2d)

# Each frame
bp_layer.update(instances, camera_pos=(cam.x, cam.y, cam.z))
fx_layer.update(fx_frame_data)
hud_layer.update(hud_primitives)
```

If you are using dynamic resolution scaling (v12), update it from perf timings:

```python
dynres.update(frame_ms=timings.total_ms)
```

---

## 3) What Codex should do next (the “make it work” checklist)

This is the exact task list you can paste into GPT-5.2 Codex.

1) Merge v13 pack into repo root (so `warbits/visual/qa` and `warbits/visual/tools/pipeline.py` land).

2) Run tests:
- `python -m pytest -q`

3) Run v13 pipeline commands:
- `python -m warbits.visual.tools.pipeline validate --strict`
- `python -m warbits.visual.tools.pipeline coverage --strict`
- `python -m warbits.visual.tools.pipeline provenance` (strict only if you already populated provenance)
- `python -m warbits.visual.tools.pipeline perfreg --frames 120 --seed 7`

4) Fix whatever fails in this order:
- Import/path issues
- Blueprint schema issues (broken JSONL lines, missing vertices/edges)
- VisualMap format issues
- Provenance omissions (add `data/visual/provenance.jsonl` entries)

5) Wire into Matplotlib renderer:
- Load registry
- Resolve visuals via VisualMap
- Render instances via MPLBlueprintLayer
- Optional: add FX and HUD layers

6) Wire into Panda3D renderer (after Matplotlib is stable).

---

## 4) Provenance (license hygiene)

Treat provenance as mandatory for any external model you ingest.

Minimum required per mesh blueprint:
- blueprint_id
- source (URL or "local pack name")
- license ("CC0", "CC-BY", etc.)
- attribution (if required)

If you don’t have this yet, run provenance in non-strict mode while prototyping:

- `python -m warbits.visual.tools.pipeline provenance`

Before shipping, flip strict on:

- `python -m warbits.visual.tools.pipeline provenance --strict`

---

## 5) What “complete” means for v13

You’re done when:
- validate passes (strict)
- coverage passes (strict)
- provenance passes (strict) OR you intentionally choose non-strict for internal builds
- perfreg produces a report reliably
- Matplotlib can render a scenario using VisualMap bindings
- Panda3D can render the same scenario using the same DB
