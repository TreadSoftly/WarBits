# warbits/physics/ballistics.py
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Tuple, TypeAlias, cast, overload

import numpy as np
import numpy.typing as npt
if TYPE_CHECKING:
    from mpl_toolkits.mplot3d import Axes3D  # type: ignore  # noqa: F401
else:
    Axes3D = Any  # type: ignore[assignment]

from ..config import settings as _cfg
from ..core.events import DebugEvent
from ..logic.state import RUNTIME
from .terrain import sample_height

__all__ = [
    # maths kernel
    "clamp_xyz_arrays",
    "simulate_bullet_trajectory",
    # scene helpers
    "reset",
    "spawn",
    "update",
]

# ───────────────────────────── type helpers ──────────────────────────────────
_F64Arr = npt.NDArray[np.float64]

if TYPE_CHECKING:
    VectorBatch: TypeAlias = _F64Arr
else:
    VectorBatch = Any  # type: ignore[assignment]

VectorLike: TypeAlias = tuple[float, float, float] | VectorBatch
_Vec3 = Tuple[float, float, float]

# ─────────────────────────── internal utilities ─────────────────────────────
def _unwrap_single(a: _F64Arr) -> _F64Arr:
    return a[0] if a.ndim == 2 and a.shape[0] == 1 else a


def _safe_empty() -> tuple[_F64Arr, _F64Arr, _F64Arr]:
    nan = np.empty(0, dtype=np.float64)
    return nan, nan, nan


def _log_physics_error(solver: str, exc: Exception, details: dict[str, Any]) -> None:
    try:
        payload: dict[str, Any] = {
            "solver": solver,
            "error": type(exc).__name__,
            "message": str(exc),
        }
        payload.update(details)
        RUNTIME.debug_events.append(
            DebugEvent(
                frame=int(RUNTIME.flight.frame),
                kind="physics_error",
                payload=payload,
            )
        )
    except Exception:
        pass


def _as_batch(v: VectorLike) -> VectorBatch:
    if isinstance(v, tuple):
        return np.asarray([v], dtype=np.float64)
    arr = np.asarray(v, dtype=np.float64)
    if arr.ndim != 2 or arr.shape[1] != 3:
        raise ValueError("vector must be shape (N,3)")
    return arr


def clamp_xyz_arrays(
    x: _F64Arr,
    y: _F64Arr,
    z: _F64Arr,
) -> tuple[_F64Arr, _F64Arr, _F64Arr]:
    try:
        n = int(min(x.shape[-1], y.shape[-1], z.shape[-1]))
        return x[..., :n], y[..., :n], z[..., :n]
    except Exception:  # pragma: no cover
        return _safe_empty()

# ───────────────────────── bullets – physics solver ─────────────────────────
@overload
def simulate_bullet_trajectory(
    plane_pos: tuple[float, float, float],
    plane_vel: tuple[float, float, float],
    *,
    muzzle_speed: float = ...,
    dt: float = ...,
    max_time: float = ...,
    drag_coefficient: float = ...,
    wind: tuple[float, float, float] | None = ...,
    gravity: float = ...,
) -> tuple[_F64Arr, _F64Arr, _F64Arr]: ...
@overload
def simulate_bullet_trajectory(
    plane_pos: VectorBatch,
    plane_vel: VectorBatch,
    *,
    muzzle_speed: float = ...,
    dt: float = ...,
    max_time: float = ...,
    drag_coefficient: float = ...,
    wind: tuple[float, float, float] | None = ...,
    gravity: float = ...,
) -> tuple[_F64Arr, _F64Arr, _F64Arr]: ...


def simulate_bullet_trajectory(
    plane_pos: VectorLike,
    plane_vel: VectorLike,
    *,
    muzzle_speed: float = _cfg.BULLET_MUZZLE_SPEED,
    dt: float = _cfg.BULLET_DT,
    max_time: float = _cfg.BULLET_MAX_TIME,
    drag_coefficient: float = _cfg.BULLET_DRAG,
    wind: tuple[float, float, float] | None = None,
    gravity: float = 9.81,
) -> tuple[_F64Arr, _F64Arr, _F64Arr]:
    try:
        if dt <= 0 or max_time <= 0 or gravity <= 0 or muzzle_speed < 0:
            raise ValueError

        p0 = _as_batch(plane_pos)
        p0[:, 2] = np.maximum(p0[:, 2], 0.0)
        v0 = _as_batch(plane_vel)

        speed_plane = np.linalg.norm(v0, axis=1, keepdims=True)
        dir_vec = np.where(
            speed_plane < 1e-6,
            np.array([[1.0, 0.0, 0.0]], dtype=np.float64),
            v0 / np.maximum(speed_plane, 1e-6),
        )

        v_init = dir_vec * (speed_plane + muzzle_speed)
        if wind is None:
            wind = RUNTIME.environment.wind
        wind_vec = np.array(wind, dtype=np.float64)

        if drag_coefficient <= 0.0 and not np.any(wind_vec):
            t_arr = np.arange(0.0, max_time + dt * 0.5, dt, dtype=np.float64)
            x = p0[:, 0:1] + v_init[:, 0:1] * t_arr
            y = p0[:, 1:2] + v_init[:, 1:2] * t_arr
            z = p0[:, 2:3] + v_init[:, 2:3] * t_arr - 0.5 * gravity * t_arr**2
            impact = z <= 0.0
            hit = np.argmax(impact, axis=1)
            t_len = t_arr.size
            hit = np.where(impact.any(axis=1), hit, t_len)
            for i in range(z.shape[0]):
                h = int(hit[i])
                if h < t_len:
                    z[i, h:] = 0.0
                    x[i, h:] = x[i, h]
                    y[i, h:] = y[i, h]
            return tuple(_unwrap_single(a) for a in (x, y, z))  # type: ignore[return-value]

        p = p0.copy()
        v = v_init.copy()
        t = np.arange(0.0, max_time + dt * 0.5, dt, dtype=np.float64)
        t_len = t.size
        x = np.empty((p.shape[0], t_len), dtype=np.float64)
        y = np.empty_like(x)
        z = np.empty_like(x)
        x[:, 0], y[:, 0], z[:, 0] = p.T

        for k in range(1, t_len):
            rel = v - wind_vec
            speed = np.linalg.norm(rel, axis=1, keepdims=True)
            if drag_coefficient > 0.0:
                v -= drag_coefficient * rel * speed * dt
            v[:, 2] -= gravity * dt
            p += v * dt
            impact = p[:, 2] <= 0.0
            p[impact, 2] = 0.0
            v[impact] = 0.0
            x[:, k], y[:, k], z[:, k] = p.T
            if impact.all():
                if k + 1 < t_len:
                    x[:, k + 1 :] = p[:, 0:1]
                    y[:, k + 1 :] = p[:, 1:2]
                    z[:, k + 1 :] = p[:, 2:3]
                break

        return tuple(_unwrap_single(a) for a in (x, y, z))  # type: ignore[return-value]
    except Exception as exc:
        if _cfg.STRICT_PHYSICS:
            raise
        _log_physics_error(
            "simulate_bullet_trajectory",
            exc,
            {
                "dt": float(dt),
                "max_time": float(max_time),
                "muzzle_speed": float(muzzle_speed),
                "drag": float(drag_coefficient),
                "gravity": float(gravity),
            },
        )
        return _safe_empty()

# ───────────────────────── bullets – scene helpers ──────────────────────────
_SPREAD_STD = np.deg2rad(max(0.0, float(_cfg.BULLET_SPREAD_DEG)))
if _SPREAD_STD > 0.0:
    _SpreadTable = np.random.normal(0.0, _SPREAD_STD, size=(8192, 3)).astype(np.float64)
else:
    _SpreadTable = np.zeros((8192, 3), dtype=np.float64)
_SpreadIdx: int = 0
_BurstCache: dict[int, tuple[_F64Arr, _F64Arr]] = {}

_BulletScatter = None                   # Path3DCollection | None  (lazy import)


def reset() -> None:
    """
    Erase all in-flight bullets and associated scatter.
    Called once per loop restart from the scene.
    """
    global _BulletScatter, _SpreadIdx
    RUNTIME.active_bullets.clear()
    _SpreadIdx = 0
    if _BulletScatter is not None:
        try:
            _BulletScatter.remove()
        except Exception:
            pass
    _BulletScatter = None


def _get_burst_buffers(bullets: int) -> tuple[_F64Arr, _F64Arr]:
    buffers = _BurstCache.get(bullets)
    if buffers is None:
        pos = np.empty((bullets, 3), dtype=np.float64)
        dirs = np.empty((bullets, 3), dtype=np.float64)
        buffers = (pos, dirs)
        _BurstCache[bullets] = buffers
    return buffers


def _next_spread(bullets: int) -> _F64Arr:
    global _SpreadIdx
    if bullets <= 0:
        return np.empty((0, 3), dtype=np.float64)
    start = _SpreadIdx
    end = start + bullets
    if end <= _SpreadTable.shape[0]:
        spreads = _SpreadTable[start:end]
    else:
        first = _SpreadTable[start:]
        remain = end - _SpreadTable.shape[0]
        second = _SpreadTable[:remain]
        spreads = np.vstack((first, second))
    _SpreadIdx = end % _SpreadTable.shape[0]
    return spreads


def _spawn_burst(
    plane_pos: _Vec3,
    plane_vel: _Vec3,
    *,
    bullets: int = 1,
    muzzle_speed: float = _cfg.BULLET_MUZZLE_SPEED,
) -> tuple[_F64Arr, _F64Arr, _F64Arr]:
    global _SpreadIdx
    if bullets < 1:
        return _safe_empty()

    # Calculate the forward velocity of the plane
    v_forw = np.array(plane_vel, dtype=np.float64)
    mag = np.linalg.norm(v_forw)
    if mag < 1e-6:  # Avoid zero velocity
        v_forw = np.array([1.0, 0.0, 0.0])  # Default direction
        mag = 1.0
    v_forw /= mag  # Normalize the forward direction

    # Apply optional spread per bullet to simulate slight inaccuracy.
    spread = _next_spread(bullets)

    p, dirs = _get_burst_buffers(bullets)
    p[:] = np.asarray(plane_pos, dtype=np.float64)
    dirs[:] = v_forw
    if spread.size:
        dirs[:] = v_forw + spread
    dirs /= np.linalg.norm(dirs, axis=1, keepdims=True)  # Normalize the perturbed direction
    dirs *= mag  # Apply perturbed velocity
    # Simulate the bullet trajectory
    bx, by, bz = simulate_bullet_trajectory(p, dirs, muzzle_speed=muzzle_speed)

    return bx, by, bz

def spawn(
    frame: int,
    plane_pos: _Vec3,
    plane_vel: _Vec3,
    ax: Axes3D,
    *,
    bullets: int = _cfg.BULLET_BURST,
) -> None:
    """
    Simulate a burst and register the resulting projectiles.
    """
    bx, by, bz = _spawn_burst(plane_pos, plane_vel, bullets=bullets)
    RUNTIME.active_bullets.add(
        bx.astype(np.float32), by.astype(np.float32), bz.astype(np.float32)
    )


def update(frame: int, ax: Axes3D) -> None:
    """
    Advance all bullets one step and keep their shared scatter marker in sync.
    """
    global _BulletScatter
    xs, ys, zs, rows = RUNTIME.active_bullets.sample_positions()
    if rows.size == 0:
        if _BulletScatter is not None:
            _BulletScatter.set_visible(False)
        return

    ground = np.asarray(sample_height(xs, ys, default=0.0), dtype=np.float32)
    impact = zs <= ground
    if impact.any():
        RUNTIME.active_bullets.remove(rows[impact])
        xs, ys, zs, rows = RUNTIME.active_bullets.sample_positions()
        if rows.size == 0:
            if _BulletScatter is not None:
                _BulletScatter.set_visible(False)
            return

    # draw / update shared scatter --------------------------------------------
    ax_any = cast(Any, ax)
    if _BulletScatter is None:
        _BulletScatter = ax_any.scatter(
            xs,
            ys,
            zs,
            color="yellow",
            marker=".",
            s=10,
            depthshade=_cfg.SCATTER_DEPTHSHADE,
        )
    else:
        _BulletScatter._offsets3d = (xs, ys, zs)     # type: ignore[attr-defined]
        _BulletScatter.set_visible(True)
    RUNTIME.active_bullets.step()
