# Visual Effects Pack v10

This pack adds **FX geometry generation + renderer layers** for the wireframe aesthetic:

- Tracers (bullets / cannon)
- Contrails / smoke trails
- Explosions (wireframe sphere)
- Impacts (wireframe starburst splat)

Everything is designed for **high FPS**:

- Hard caps (pools) so FX can't explode your frame time
- Deterministic RNG (so replays look identical)
- Renderer-side **preallocated color buffers** to reduce per-frame allocations

---

## What this pack adds

### Core FX (renderer agnostic)

`warbits/visual/effects/`

- `FxManager`: owns all FX pools and emits a `FxFrameData` each frame.
- `TrailRingBuffer`: tracks last N positions for many objects and emits faded segments.
- `ExplosionPool`: pooled expanding wireframe spheres.
- `BurstPool`: pooled starbursts aligned to impact normals.

### Matplotlib renderer layer

`warbits/visual/mpl/effects_layer.py`

- `MplFxLayer`: consumes `FxFrameData` and updates a small set of `Line3DCollection` artists.

### Panda3D renderer layer

`warbits/visual/panda3d/effects_layer.py`

- `P3DFxLayer`: consumes `FxFrameData` and updates a `LineBatch` per layer.

---

## Minimal integration recipe

### 1) Create an `FxManager`

Do this once when you set up the renderer:

```python
from warbits.visual.effects import FxConfig, FxManager

fx = FxManager(FxConfig())
```

### 2) Feed it projectile positions (for tracers)

Each frame:

```python
fx.update_tracers(ids=bullet_ids, positions=bullet_positions_xyz, frame_idx=frame)
```

You can use **any** ids. The system internally maps ids to slots.

### 3) Spawn explosions / impacts from your event log

```python
fx.spawn_explosion(center=(x,y,z), frame_idx=frame, max_radius_m=25.0)
fx.spawn_impact(center=(x,y,z), normal=(nx,ny,nz), frame_idx=frame, radius_m=6.0)
```

Or pipe dictionaries:

```python
fx.ingest_event_dicts(events, frame_idx=frame)
```

### 4) Build frame geometry

```python
fx_frame = fx.build_frame(frame_idx=frame)
```

### 5) Render

Matplotlib:

```python
layer.update(fx_frame)
```

Panda3D:

```python
p3d_fx_layer.update(fx_frame)
```

---

## Performance knobs you should actually use

- `FxConfig.max_tracer_objects` and `FxConfig.max_tracer_segments`

  This is the big one. If you fire 10,000 rounds per second, don't try to draw 10,000 tracer trails.

- `FxConfig.tracer_history`

  If you want the “laser stitch” vibe, increase this. If you want *raw FPS*, keep it 2–3.

- `FxConfig.explosion_lat_steps/lon_steps`

  This controls sphere segment count.

---

## Next packs

- v11: HUD + targeting/radar primitives integrated into the same visual runtime
- v12: performance harness + profiling targets + LOD rules
- v13: packaging + data-driven accuracy loops
