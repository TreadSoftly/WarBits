# C:\Users\MrDra\OneDrive\Desktop\warbits\warbits\physics\explosions.py
from __future__ import annotations
# ─────────────────────────────────────────────────────────────────────────────
# physics/explosions.py – centralised explosion VFX (moved from scene.effects)
# ─────────────────────────────────────────────────────────────────────────────
from collections import deque
from typing import Any, Tuple, cast

import numpy as np
from numpy.typing import NDArray
from matplotlib.axes import Axes
from mpl_toolkits.mplot3d.art3d import Poly3DCollection  # type: ignore

from ..config import settings as _cfg

# 1 · Unit-sphere vertices ----------------------------------------------------
_LAT, _LON = _cfg.SPHERE_LAT, _cfg.SPHERE_LON
_th, _ph = np.mgrid[0:np.pi:complex(_LAT), 0:2 * np.pi:complex(_LON)]
_UNIT: NDArray[np.float32] = (
    np.stack(
        [np.sin(_th) * np.cos(_ph), np.sin(_th) * np.sin(_ph), np.cos(_th)],
        axis=-1,
    )
    .reshape(-1, 3)
    .astype(np.float32)
)
_STEP = _LON - 1
_QUAD_IDX = (
    np.arange((_LAT - 1) * _STEP, dtype=np.int32).reshape(-1, 1)
    + np.array([0, 1, 1 + _STEP, _STEP], dtype=np.int32)
)
_SPHERE_FACES: NDArray[np.float32] = _UNIT[_QUAD_IDX]
_RING_POINTS = 60
_RING_THETA = np.linspace(0.0, 2.0 * np.pi, _RING_POINTS, dtype=np.float32)
_RING_UNIT = np.stack([np.cos(_RING_THETA), np.sin(_RING_THETA)], axis=1).astype(np.float32)

_ax: Axes | None = None

__all__ = ["register_axes", "spawn_explosion", "update_explosion", "active_count"]

# --------------------------------------------------------------------------- #
# 2 · Generic helpers
# --------------------------------------------------------------------------- #
def register_axes(ax: Axes) -> None:
    """
    Register the Matplotlib Axes3D instance so explosions can be rendered.
    Call this once during scene initialisation.
    """
    global _ax, _EXP_POOL, _EXP_ACTIVE, _SHOCK_POOL, _SHOCK_ACTIVE
    if _ax is not None and _ax is not ax:
        for exp in (*_EXP_POOL, *_EXP_ACTIVE):
            try:
                exp.poly.remove()
            except Exception:
                pass
        _EXP_POOL.clear()
        _EXP_ACTIVE.clear()
        for shock in (*_SHOCK_POOL, *_SHOCK_ACTIVE):
            try:
                shock.line.remove()
            except Exception:
                pass
        _SHOCK_POOL.clear()
        _SHOCK_ACTIVE.clear()
    _ax = ax

# --------------------------------------------------------------------------- #
# 3 · Explosion object-pool
# --------------------------------------------------------------------------- #
class _Explosion:
    __slots__ = ("poly", "frame", "cx", "cy", "cz", "_center", "_verts", "_scale", "_style")

    def __init__(self, poly: Poly3DCollection) -> None:
        self.poly: Any = poly
        self.frame = 0
        self.cx = self.cy = self.cz = 0.0
        self._center = np.zeros(3, dtype=np.float32)
        self._verts: NDArray[np.float32] = _SPHERE_FACES.copy()
        self._scale = 1.0
        self._style = "sphere"

    def reset(self, centre: Tuple[float, float, float], *, scale: float = 1.0, style: str = "sphere") -> None:
        self.cx, self.cy, self.cz = centre
        self.frame = 0
        self._scale = max(0.1, float(scale))
        self._style = str(style)
        self._center[:] = (self.cx, self.cy, self.cz)
        self.poly.set_alpha(1.0)
        self.poly.set_visible(True)

    def update(self) -> bool:
        """Advance one frame.  Return *True* while alive."""
        frac = self.frame / _EXP_LIMIT
        base_r = np.float32((25.0 + 125.0 * frac) * self._scale)
        if self._style == "mushroom":
            scale_xy = base_r * np.float32(1.25)
            scale_z = base_r * np.float32(0.9)
            self._verts[:] = _SPHERE_FACES
            self._verts[..., 0] *= scale_xy
            self._verts[..., 1] *= scale_xy
            self._verts[..., 2] *= scale_z
            stem = self._verts[..., 2] < 0.0
            self._verts[stem, 0] *= 0.35
            self._verts[stem, 1] *= 0.35
            self._verts[stem, 2] *= 1.6
            lift = base_r * np.float32(0.35 + 0.35 * frac)
            self._center[:] = (self.cx, self.cy, self.cz + float(lift))
        else:
            np.multiply(_SPHERE_FACES, base_r, out=self._verts)
            self._center[:] = (self.cx, self.cy, self.cz)
        self._verts += self._center
        self.poly.set_verts(cast(Any, self._verts))
        self.poly.set_facecolor((1.0, 0.9 - 0.9 * frac, 0.0, 1.0 - frac))  # type: ignore[arg-type]
        self.poly.set_edgecolor("orange")  # type: ignore[arg-type]
        self.frame += 1
        if self.frame >= _EXP_LIMIT:
            self.poly.set_visible(False)
            return False
        return True


_EXP_LIMIT = 30
_EXP_POOL: deque[_Explosion] = deque()
_EXP_ACTIVE: list[_Explosion] = []
_SHOCK_LIMIT = 24


class _Shockwave:
    __slots__ = ("line", "frame", "cx", "cy", "cz", "_max_r", "_verts", "_zs")

    def __init__(self, line: Any) -> None:
        self.line = line
        self.frame = 0
        self.cx = self.cy = self.cz = 0.0
        self._max_r = 1.0
        self._verts = np.zeros((_RING_POINTS, 2), dtype=np.float32)
        self._zs = np.zeros(_RING_POINTS, dtype=np.float32)

    def reset(self, centre: Tuple[float, float, float], *, max_radius: float) -> None:
        self.cx, self.cy, self.cz = centre
        self.frame = 0
        self._max_r = max(1.0, float(max_radius))
        self.line.set_alpha(0.9)
        self.line.set_visible(True)

    def update(self) -> bool:
        frac = self.frame / _SHOCK_LIMIT
        radius = self._max_r * frac
        np.multiply(_RING_UNIT, radius, out=self._verts)
        self._verts[:, 0] += self.cx
        self._verts[:, 1] += self.cy
        self._zs.fill(self.cz)
        self.line.set_data(self._verts[:, 0], self._verts[:, 1])
        self.line.set_3d_properties(self._zs)
        self.line.set_alpha(max(0.0, 0.9 - frac))
        self.frame += 1
        if self.frame >= _SHOCK_LIMIT:
            self.line.set_visible(False)
            return False
        return True


_SHOCK_POOL: deque[_Shockwave] = deque()
_SHOCK_ACTIVE: list[_Shockwave] = []


def _spawn_shockwave(centre: Tuple[float, float, float], *, scale: float) -> None:
    if _ax is None:
        return
    max_radius = max(150.0, 260.0 * float(scale))
    ax_any = cast(Any, _ax)
    shock = (
        _SHOCK_POOL.popleft()
        if _SHOCK_POOL
        else _Shockwave(ax_any.plot([], [], [], color="orange", linewidth=2, alpha=0.8)[0])
    )
    shock.reset((centre[0], centre[1], centre[2] + 2.0), max_radius=max_radius)
    _SHOCK_ACTIVE.append(shock)

# --------------------------------------------------------------------------- #
# 4 · Public façade
# --------------------------------------------------------------------------- #
def spawn_explosion(
    centre: Tuple[float, float, float],
    *,
    scale: float = 1.0,
    style: str = "sphere",
) -> None:
    """Spawn a new explosion centred at *(x, y, z)* (no-op if axes unregistered)."""
    if _ax is None:
        return
    exp = (
        _EXP_POOL.popleft()
        if _EXP_POOL
        else _Explosion(Poly3DCollection([], facecolor="white", edgecolor="orange", alpha=1.0))
    )
    if exp.poly not in _ax.collections:
        _ax.add_collection3d(exp.poly)  # type: ignore[arg-type]
    exp.reset(centre, scale=scale, style=style)
    _EXP_ACTIVE.append(exp)
    if style in {"mushroom", "nuke"}:
        _spawn_shockwave(centre, scale=scale)


def update_explosion() -> None:
    """Advance all active explosions by one frame."""
    alive: list[_Explosion] = []
    for e in _EXP_ACTIVE:
        if e.update():
            alive.append(e)
        else:
            _EXP_POOL.append(e)
    _EXP_ACTIVE[:] = alive
    alive_shock: list[_Shockwave] = []
    for s in _SHOCK_ACTIVE:
        if s.update():
            alive_shock.append(s)
        else:
            _SHOCK_POOL.append(s)
    _SHOCK_ACTIVE[:] = alive_shock


def active_count() -> int:
    return len(_EXP_ACTIVE) + len(_SHOCK_ACTIVE)
