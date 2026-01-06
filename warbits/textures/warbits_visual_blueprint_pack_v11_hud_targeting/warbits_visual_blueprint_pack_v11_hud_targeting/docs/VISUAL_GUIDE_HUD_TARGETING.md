# Visual System v11 — HUD + Targeting

This pack adds a **renderer-agnostic HUD builder** plus **Matplotlib + Panda3D overlay renderers**.

The design is intentionally simple:

1. Build a `HudContext` from your sim state.
2. Choose a `ScreenProjector` (renderer-specific, or use `PinholeProjector` fallback).
3. Use `HudBuilder.build(ctx, projector)` to produce a `HudDrawList`.
4. Feed that draw list to a renderer overlay:
   - `warbits.visual.mpl.hud_overlay.MplHudOverlay`
   - `warbits.visual.panda3d.hud_overlay.P3DHudOverlay`

## What you get (War Thunder-ish baseline)

- Speed / altitude / heading text
- Crosshair
- Simple horizon/pitch cue
- Target box + range label
- Lead pipper (circle) based on simple intercept math

## Matplotlib integration pattern

```python
from warbits.visual.hud import HudBuilder, HudTheme
from warbits.visual.hud.projector import PinholeProjector
from warbits.visual.hud.adapters import build_context_from_warbits_state
from warbits.visual.mpl.hud_overlay import MplHudOverlay

# once
hud_overlay = MplHudOverlay(fig)
hud_builder = HudBuilder(theme=HudTheme(pixel_snap=0))

# per frame
ctx = build_context_from_warbits_state(
    state,
    time_s=sim_time,
    camera_pos_m=camera_pos,
    camera_forward=camera_forward,
    camera_up=camera_up,
    fov_y_deg=55.0,
    aspect=16/9,
    selected_track_id=None,
)
projector = PinholeProjector(ctx.camera)
drawlist = hud_builder.build(ctx, projector)
hud_overlay.update(drawlist)
```

### Performance notes (Matplotlib)

- The overlay uses a **single 2D axes** and reuses artists.
- Keep the number of HUD primitives small.
- The *3D scene* still dominates your frame time in Matplotlib; the HUD won't.

## Panda3D integration pattern

In Panda3D you attach the overlay to `aspect2d`:

```python
from warbits.visual.panda3d.hud_overlay import P3DHudOverlay

hud_overlay = P3DHudOverlay(parent_2d=base.aspect2d)

# per frame
hud_overlay.update(drawlist)
```

The Panda3D overlay uses a **dynamic line Geom** (preallocated vertices) to avoid per-frame node churn.

## Next steps

- v12 will add **LOD policy + draw call batching**.
- v13 will expand **data-driven visual accuracy** and packaging.
