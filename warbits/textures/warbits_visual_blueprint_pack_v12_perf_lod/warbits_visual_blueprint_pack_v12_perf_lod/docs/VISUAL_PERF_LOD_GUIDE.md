# WarBits Visual Blueprint System — Performance + LOD Guide (v12)

This pack adds two things that make the **visual system scale** without turning into a frame-time horror movie:

1) **A low-allocation frame timing harness** you can plug into Matplotlib and Panda3D renderers.
2) **A deterministic LOD policy** (level-of-detail switching) so far-away stuff gets cheaper automatically.

None of this changes simulation truth. It only controls how expensive the *view layer* is.

---

## What you get

### `warbits.visual.perf`

- `VisualStage`: an enum of timing buckets (terrain, entities, projectiles, hud, effects).
- `VisualFrameTimer`: low-allocation timing collection for one frame.
- `VisualBudget`: a **soft** budget (tripwire) you can use to detect regression.

### `warbits.visual.lod`

- `LODLevel`: `HIGH`, `MED`, `LOW`, `ICON`.
- `LODPolicy`: deterministic selection rules.
- `projected_radius_px(...)`: estimate how big an object appears on screen.

### `warbits.visual.batch`

- `ProjectileSegments`: fast numpy helpers to produce line segments from projectile state.
- Optional wrappers designed to feed:
  - Matplotlib `Line3DCollection.set_segments(...)`
  - Panda3D `GeomLines` batch buffers

---

## How to integrate

### 1) Add a per-frame timer to your renderer

Pseudo-code (works in concept for both renderers):

```python
from warbits.visual.perf import VisualFrameTimer, VisualStage

class MyRenderer:
    def __init__(self):
        self.timer = VisualFrameTimer()

    def draw_frame(self, frame_idx, sim_state):
        self.timer.begin(frame_idx)

        self.timer.stage_begin(VisualStage.TERRAIN)
        self.draw_terrain(sim_state)
        self.timer.stage_end(VisualStage.TERRAIN)

        self.timer.stage_begin(VisualStage.ENTITIES)
        self.draw_entities(sim_state)
        self.timer.stage_end(VisualStage.ENTITIES)

        self.timer.stage_begin(VisualStage.PROJECTILES)
        self.draw_projectiles(sim_state)
        self.timer.stage_end(VisualStage.PROJECTILES)

        self.timer.stage_begin(VisualStage.HUD)
        self.draw_hud(sim_state)
        self.timer.stage_end(VisualStage.HUD)

        self.timer.stage_begin(VisualStage.EFFECTS)
        self.draw_effects(sim_state)
        self.timer.stage_end(VisualStage.EFFECTS)

        sample = self.timer.end()
        # `sample` includes per-stage ns plus total.
```

Why the manual begin/end calls?

- It avoids context-manager overhead in hot loops.
- It keeps allocations predictable.

### 2) Use LOD policy to pick blueprint LOD

```python
from warbits.visual.lod import LODPolicy, projected_radius_px

lod_policy = LODPolicy.defaults()

# Suppose you know camera properties (or approximate them):
viewport_h_px = 1080
fov_y_rad = 60.0 * 3.14159 / 180.0

radius_m = 7.5
distance_m = 2500.0
px = projected_radius_px(radius_m, distance_m, fov_y_rad, viewport_h_px)
level = lod_policy.select(distance_m=distance_m, projected_radius_px=px)
```

`LODPolicy` is deterministic: same inputs ⇒ same level.

### 3) Batch projectile segments instead of per-projectile artists/nodes

For bullets/rockets, the cheapest visual is a short line segment from last position to current.

```python
import numpy as np
from warbits.visual.batch import segments_from_positions

# prev and curr are (N,3) float arrays
segs = segments_from_positions(prev, curr)
# segs is (N,2,3)
```

Matplotlib:

- Keep **one** `Line3DCollection` for all bullets.
- Update its segments each frame.

Panda3D:

- Keep **one** `Geom` batch for all bullet segments.
- Update the vertex buffer in place.

---

## Performance rules this pack assumes

- **No per-frame object creation** for “many things”:
  - bullets, tracers, debris, fragments
  - labels on dozens of targets

- Prefer “update arrays in place” over “build new lists”.

- LOD must be a **policy**, not a scattering of `if distance > ...` across files.

---

## What this pack does *not* do

- It does not decide “what a vehicle looks like”. That’s the blueprint DB.
- It does not change physics.
- It does not enforce a hard FPS limit.

Budgets are tripwires for regression checks — not a governor.


---

## Suggested budgets (tripwires, not hard caps)

Budgets are *not* “thou shalt never exceed.” They are a way to notice when a change quietly doubles visual cost.

A sane starting point for dev machines:

- Terrain: ~2–4 ms
- Entities (air/ground): ~2–4 ms
- Projectiles: ~1–3 ms
- HUD: ~0.2–1 ms
- Effects: ~0.5–2 ms

If you’re chasing >120 FPS, cut those in half.

The pack includes a `VisualBudget.defaults()` helper.

---

## LOD strategy (wireframe style)

The wireframe look is friendly to LOD because the *silhouette* matters most.

Recommended LOD content:

- `HIGH`: full feature edges + some ribs (primary + secondary)
- `MED`: only feature edges (ridges + boundaries)
- `LOW`: coarse feature edges (decimated) or proxy hull
- `ICON`: a single marker + optional heading tick

In the visual style you described, `ICON` can still look good (bright green blip with a tiny orientation notch).

---

## Panda3D note: dynamic resolution scaling

If you implement render-to-texture (already in the Panda3D packs), you can add **dynamic resolution scaling**:

- If average frame time increases, drop render resolution scale from 1.0 → 0.85 → 0.70.
- If frame time stays low for a while, raise it back slowly.

This is optional, but it’s a practical way to keep frame pacing smooth when you spawn thousands of tracer segments.

