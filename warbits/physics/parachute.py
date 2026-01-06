# ── warbits/physics/parachute.py ────────────────────────────────────────────
from __future__ import annotations

from collections import deque
import math
from typing import Any, List, Tuple, cast

import numpy as np
import numpy.typing as npt
from mpl_toolkits.mplot3d import Axes3D          # type: ignore
from mpl_toolkits.mplot3d.art3d import (  # type: ignore
    Poly3DCollection,
    Line3DCollection,
)                                               # type: ignore

from ..config import settings as _cfg
from ..logic.state import RUNTIME

__all__ = [
    "register_axes",
    "spawn_parachute",
    "update_parachute",
    "reset_parachute",
    "active_count",
]

# ─────────────────────────────────────────────────────────────────────────────
# 1 · Axes registry (scene must call this once at start-up)
# ─────────────────────────────────────────────────────────────────────────────
_ax: Axes3D | None = None


def register_axes(ax: Axes3D) -> None:
    global _ax, _POOL, _ACTIVE
    if _ax is not None and _ax is not ax:
        for pc in (*_ACTIVE, *_POOL):
            for art in (pc.canopy, pc.cords, pc.pilot, pc.plume):
                try:
                    art.remove()
                except Exception:
                    pass
        _POOL.clear()
        _ACTIVE.clear()
    _ax = ax


# ─────────────────────────────────────────────────────────────────────────────
# 2 · Cached unit-sphere vertices  (lat×lon = 15×30)
# ─────────────────────────────────────────────────────────────────────────────
_LAT, _LON = _cfg.SPHERE_LAT, _cfg.SPHERE_LON
_th, _ph = np.mgrid[0:np.pi:complex(_LAT), 0:2 * np.pi:complex(_LON)]
_F32Arr = npt.NDArray[np.float32]

_UNIT: _F32Arr = (
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
_SPHERE_FACES: _F32Arr = _UNIT[_QUAD_IDX]
_HEMI_FACES: _F32Arr = _SPHERE_FACES[np.min(_SPHERE_FACES[..., 2], axis=1) >= 0.0]
_PILOT_TOP_UNIT: _F32Arr = np.array(
    [
        (-0.5, -0.5, 0.0),
        (0.5, -0.5, 0.0),
        (0.5, 0.5, 0.0),
        (-0.5, 0.5, 0.0),
    ],
    dtype=np.float32,
)
_ANCHOR_UNIT: _F32Arr = np.array(
    [
        (-1.0, 0.0, 0.0),
        (1.0, 0.0, 0.0),
        (0.0, -1.0, 0.0),
        (0.0, 1.0, 0.0),
    ],
    dtype=np.float32,
)

# ─────────────────────────────────────────────────────────────────────────────
# 3 · Parachute + ejection sequence
# ─────────────────────────────────────────────────────────────────────────────
class _Parachute:
    # Dimensions (world-units)
    _RADIUS = 175.0                   # canopy radius   (edge ≈ 280 u)
    _HANG   = 460.0                   # canopy rim → pilot-top gap
    _P_W    = 100.0                    # pilot block width
    _P_H    = 200.0                   # pilot block height
    _CORD_W = 7.0
    _DROP   = 10.0                    # normal descent (u/frame)

    # Timings
    _T_BOOST   = 6                    # rocket-seat frames
    _T_FREEFALL = 8                   # free-fall before canopy inflates
    _T_INFLATE = 8                    # frames to fully open

    cx: float
    cy: float
    cz: float
    vx: float
    vy: float
    vz: float
    stage: int
    stage_tick: int

    def __init__(self) -> None:
        if _ax is None:
            raise RuntimeError("call register_axes() first")

        edge = (0.35, 0.35, 0.35, 1)  # mid-grey outline
        self.canopy = Poly3DCollection([], facecolor="white",
                                    edgecolor=edge, linewidths=0.9, alpha=1.0)
        self.cords  = Line3DCollection([], colors="black",
                                    linewidths=self._CORD_W, alpha=1.0)
        self.cords.set_segments([[(0, 0, 0), (0, 0, 0)]])       # placeholder
        self.pilot  = Poly3DCollection([], facecolor="red",
                                    edgecolor="black", linewidths=1.0, alpha=1.0)
        # yellow rocket plume (single quad)
        self.plume  = Poly3DCollection([], facecolor="yellow",
                                    edgecolor="none", alpha=1.0)

        for art in (self.canopy, self.cords, self.pilot, self.plume):
            _ax.add_collection3d(art)                           # type: ignore[arg-type]

        self._center = np.zeros(3, dtype=np.float32)
        self._anchor_center = np.zeros(3, dtype=np.float32)
        self._pilot_top_base = _PILOT_TOP_UNIT * np.float32(self._P_W)
        self._pilot_top = np.empty_like(_PILOT_TOP_UNIT)
        self._pilot_bot = np.empty_like(_PILOT_TOP_UNIT)
        self._pilot_faces = [self._pilot_top, self._pilot_bot]
        self._canopy_faces = np.empty_like(_HEMI_FACES)
        self._canopy_faces_scaled = np.empty_like(_HEMI_FACES)
        self._cord_anchors = np.empty((_ANCHOR_UNIT.shape[0], 3), dtype=np.float32)
        self._cord_anchors_scaled = np.empty_like(_ANCHOR_UNIT)
        self._cord_target = np.empty(3, dtype=np.float32)
        self._cord_segments = np.empty((_ANCHOR_UNIT.shape[0], 2, 3), dtype=np.float32)
        self._plume_verts = np.empty((3, 3), dtype=np.float32)
        self._plume_faces = [self._plume_verts]
        self._radius_cached = -1.0
        self._rim_radius_cached = -1.0

        # Runtime state
        self.cx = self.cy = self.cz = 0.0
        self.vx = self.vy = self.vz = 0.0
        self.stage      = 0          # 0-boost | 1-freefall | 2-inflate | 3-glide
        self.stage_tick = 0

    # --------------------------------------------------------------------- #
    def reset(self, centre: Tuple[float, float, float]) -> None:
        self.cx, self.cy, z0 = centre
        self.cz        = max(z0, 300.0)        # always visible height
        self.vx = self.vy = self.vz = 0.0
        self.stage     = 0
        self.stage_tick = 0
        self._radius_cached = -1.0
        self._rim_radius_cached = -1.0
        # visibility
        self._show(self.pilot, True)
        self._show(self.plume, True)
        self._show(self.canopy, False)
        self._show(self.cords,  False)

    # --------------------------------------------------------------------- #
    def _show(self, art: Poly3DCollection | Line3DCollection, visible: bool) -> None:
        art.set_visible(visible)
        if visible:
            art.set_alpha(1.0)

    # --------------------------------------------------------------------- #
    def update(self) -> bool:
        use_physics = _cfg.PARACHUTE_PHYSICS
        dt_s = max(float(_cfg.SIM_DT_MS) / 1000.0, 1e-6)
        # ── 0 · rocket-seat boost ───────────────────────────────────────
        if self.stage == 0:
            self.cz += 35.0                    # strong upward kick
            x, y = self._wind_sway()
            self._update_pilot(x, y)
            self._update_plume(x, y)
            self.stage_tick += 1
            if self.stage_tick >= self._T_BOOST:
                self.stage, self.stage_tick = 1, 0
                self._show(self.plume, False)
            return True

        # ── 1 · short free-fall (no canopy) ─────────────────────────────
        if self.stage == 1:
            self.cz -= 22.0                    # faster drop
            x, y = self._wind_sway()
            self._update_pilot(x, y)
            self.stage_tick += 1
            if self.stage_tick >= self._T_FREEFALL:
                self.stage, self.stage_tick = 2, 0
                if use_physics:
                    self.vx = 0.0
                    self.vy = 0.0
                    self.vz = -22.0 / dt_s
                self._show(self.canopy, True)
                self._show(self.cords,  True)
            return True

        # ── 2 · inflate canopy (radius grows) ───────────────────────────
        if self.stage == 2:
            frac = (self.stage_tick + 1) / self._T_INFLATE
            if use_physics:
                drag = _cfg.PARACHUTE_DRAG_CLOSED + (
                    (_cfg.PARACHUTE_DRAG_OPEN - _cfg.PARACHUTE_DRAG_CLOSED) * frac
                )
                self._physics_step(drag, dt_s)
            else:
                self.cz -= self._DROP * 0.4
            x, y = self._wind_sway()
            self._update_canopy(frac, x, y)
            self._update_pilot(x, y)
            self.stage_tick += 1
            if self.stage_tick >= self._T_INFLATE:
                self.stage, self.stage_tick = 3, 0
            return True

        # ── 3 · normal glide to ground ──────────────────────────────────
        if self.stage == 3:
            if use_physics:
                self._physics_step(_cfg.PARACHUTE_DRAG_OPEN, dt_s)
            else:
                self.cz -= self._DROP
            if self.cz <= 0.0:
                for art in (self.canopy, self.cords, self.pilot):
                    art.set_visible(False)
                return False
            x, y = self._wind_sway()
            self._update_canopy(1.0, x, y)
            self._update_pilot(x, y)
            return True

        return False  # should never reach here


    def _physics_step(self, drag: float, dt_s: float) -> None:
        wind_x, wind_y, wind_z = RUNTIME.environment.wind
        rel_x = self.vx - wind_x
        rel_y = self.vy - wind_y
        rel_z = self.vz - wind_z
        speed = math.sqrt(rel_x * rel_x + rel_y * rel_y + rel_z * rel_z)
        if drag > 0.0 and speed > 1e-6:
            scale = drag * speed * dt_s
            self.vx -= rel_x * scale
            self.vy -= rel_y * scale
            self.vz -= rel_z * scale
        self.vz -= _cfg.PARACHUTE_GRAVITY * dt_s
        self.cx += self.vx * dt_s
        self.cy += self.vy * dt_s
        self.cz += self.vz * dt_s

    # ------------------------------------------------------------------ #
    #  ✦ low-level geometry helpers ✦
    # ------------------------------------------------------------------ #
    def _wind_sway(self) -> tuple[float, float]:
        t = self.stage_tick
        base = 0 if self.stage == 0 else self._T_BOOST  # continuous sway
        phase = base + t
        x = self.cx + 22.0 * math.sin(0.09 * phase)
        y = self.cy + 22.0 * math.cos(0.07 * phase)
        return x, y

    def _update_pilot(self, x: float, y: float) -> None:
        p_top = self.cz - self._HANG if self.stage >= 2 else self.cz
        self._center[0] = x
        self._center[1] = y
        self._center[2] = p_top
        np.add(self._pilot_top_base, self._center, out=self._pilot_top)
        np.copyto(self._pilot_bot, self._pilot_top)
        self._pilot_bot[:, 2] -= np.float32(self._P_H)
        self.pilot.set_verts(cast(Any, self._pilot_faces))

    def _update_canopy(self, frac: float, x: float, y: float) -> None:
        """`frac` ∈ [0,1] – 0: closed, 1: fully open."""
        radius = float(self._RADIUS * frac)
        radius_f = np.float32(radius)
        base_z = np.float32(self.cz - radius)
        self._center[:] = (x, y, base_z)
        if abs(radius - self._radius_cached) > 1e-6:
            np.multiply(_HEMI_FACES, radius_f, out=self._canopy_faces_scaled)
            self._radius_cached = radius
        np.add(self._canopy_faces_scaled, self._center, out=self._canopy_faces)
        self.canopy.set_verts(cast(Any, self._canopy_faces))

        # cords
        rim_r = radius * 0.82
        rim_r_f = np.float32(rim_r)
        p_top = np.float32(self.cz - self._HANG)
        self._anchor_center[:] = (x, y, base_z)
        if abs(rim_r - self._rim_radius_cached) > 1e-6:
            np.multiply(_ANCHOR_UNIT, rim_r_f, out=self._cord_anchors_scaled)
            self._rim_radius_cached = rim_r
        np.add(self._cord_anchors_scaled, self._anchor_center, out=self._cord_anchors)
        self._cord_target[:] = (x, y, p_top)
        self._cord_segments[:, 0, :] = self._cord_anchors
        self._cord_segments[:, 1, :] = self._cord_target
        self.cords.set_segments(cast(Any, self._cord_segments))

    def _update_plume(self, x: float, y: float) -> None:
        """Yellow quad under the pilot while the rocket motor fires."""
        p_bot = self.cz - self._P_H
        phase = float(self.stage_tick)
        flicker = 0.5 + 0.5 * math.sin(0.6 * phase)
        size = np.float32(30.0 + 5.0 * flicker)
        half = size * np.float32(0.5)
        self._plume_verts[0] = (x - half, y, p_bot)
        self._plume_verts[1] = (x + half, y, p_bot)
        self._plume_verts[2] = (x, y, p_bot - size)
        self.plume.set_verts(cast(Any, self._plume_faces))


# ─────────────────────────────────────────────────────────────────────────────
# 4 · Simple object pool (to avoid per-frame allocations)
# ─────────────────────────────────────────────────────────────────────────────
_POOL: deque[_Parachute] = deque()
_ACTIVE: List[_Parachute] = []


def _get() -> _Parachute:
    return _POOL.popleft() if _POOL else _Parachute()


# ─────────────────────────────────────────────────────────────────────────────
# 5 · Public façade
# ─────────────────────────────────────────────────────────────────────────────
def spawn_parachute(centre: Tuple[float, float, float]) -> None:
    if _ax is None:
        return
    obj = _get()
    obj.reset(centre)
    _ACTIVE.append(obj)


def update_parachute() -> None:
    alive: List[_Parachute] = []
    for pc in _ACTIVE:
        (alive if pc.update() else _POOL).append(pc)
    _ACTIVE[:] = alive


def reset_parachute() -> None:
    for pc in (*_ACTIVE, *_POOL):
        for art in (pc.canopy, pc.cords, pc.pilot, pc.plume):
            art.set_visible(False)
    _POOL.extend(_ACTIVE)
    _ACTIVE.clear()


def active_count() -> int:
    return len(_ACTIVE)
