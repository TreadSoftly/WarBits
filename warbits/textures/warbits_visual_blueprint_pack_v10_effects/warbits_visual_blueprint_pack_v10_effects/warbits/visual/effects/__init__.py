"""Visual effects (FX) systems for WarBits wireframe renderers.

This package is intentionally **renderer-agnostic**.

- It produces *geometry batches* (line segments + alpha) for FX like tracers,
  contrails / smoke trails, explosions, and impact bursts.
- Renderers (Matplotlib / Panda3D) consume those batches and draw them efficiently.

Design goals
------------
- Deterministic under a fixed seed (if you use deterministic inputs).
- Pooling + fixed caps to keep frametime smooth.
- No hard dependency on Matplotlib or Panda3D.

Typical usage
-------------
1) Create an :class:`~warbits.visual.effects.manager.FxManager`.
2) Each frame:
   - feed it projectile/aircraft positions (optional)
   - feed it sim events (ExplosionEvent, ImpactEvent, etc.)
   - call :meth:`~warbits.visual.effects.manager.FxManager.build_frame`
3) Hand the resulting :class:`~warbits.visual.effects.types.FxFrameData` to
   the renderer-specific layer:

- Matplotlib: :class:`warbits.visual.mpl.effects_layer.MplFxLayer`
- Panda3D: :class:`warbits.visual.panda3d.effects_layer.P3DFxLayer`

"""

from .config import FxConfig
from .explosions import ExplosionParams, ExplosionPool
from .manager import FxManager
from .trails import TrailParams, TrailRingBuffer
from .types import FxFrameData

__all__ = [
    "FxConfig",
    "FxFrameData",
    "FxManager",
    "TrailParams",
    "TrailRingBuffer",
    "ExplosionParams",
    "ExplosionPool",
]
