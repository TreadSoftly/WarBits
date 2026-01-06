# ── warbits/physics/rockets.py ────────────────────────────────────────────
from __future__ import annotations

import bisect
from typing import TYPE_CHECKING, Any, List, Tuple, TypeAlias, cast, overload

import numpy as np
import numpy.typing as npt
if TYPE_CHECKING:
    from mpl_toolkits.mplot3d import Axes3D  # type: ignore  # noqa: F401
else:
    Axes3D = Any  # type: ignore[assignment]

from ..config import settings as _cfg
from ..core.events import DebugEvent, ImpactEvent
from ..logic.state import RUNTIME
from .terrain import sample_height
__all__ = [
    # low-level physics kernel
    "simulate_rocket_trajectory",
    # scene façade
    "schedule_launch",
    "reset",
    "step",
]

# ───────────────────────────── type helpers ───────────────────────────────
_F64Arr = npt.NDArray[np.float64]

if TYPE_CHECKING:
    VectorBatch: TypeAlias = _F64Arr
else:
    VectorBatch = Any  # type: ignore[assignment]

VectorLike: TypeAlias = tuple[float, float, float] | VectorBatch
_Vec3 = Tuple[float, float, float]

# ───────────────────────── internal utilities ─────────────────────────────
def _unwrap_single(a: _F64Arr) -> _F64Arr:  # squeeze (1,T) → (T,)
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


# ───────────────────────── physics kernel ────────────────────────────────
@overload
def simulate_rocket_trajectory(
    plane_pos: tuple[float, float, float],
    plane_vel: tuple[float, float, float],
    *,
    rocket_speed: float = ...,
    dt: float = ...,
    max_time: float = ...,
    thrust_dur: float = ...,
    drag_coefficient: float = ...,
    wind: tuple[float, float, float] | None = ...,
    mass_initial: float = ...,
    mass_dry: float = ...,
    mass_flow: float = ...,
    gravity: float = ...,
) -> tuple[_F64Arr, _F64Arr, _F64Arr]: ...
@overload
def simulate_rocket_trajectory(
    plane_pos: VectorBatch,
    plane_vel: VectorBatch,
    *,
    rocket_speed: float = ...,
    dt: float = ...,
    max_time: float = ...,
    thrust_dur: float = ...,
    drag_coefficient: float = ...,
    wind: tuple[float, float, float] | None = ...,
    mass_initial: float = ...,
    mass_dry: float = ...,
    mass_flow: float = ...,
    gravity: float = ...,
) -> tuple[_F64Arr, _F64Arr, _F64Arr]: ...


def simulate_rocket_trajectory(
    plane_pos: VectorLike,
    plane_vel: VectorLike,
    *,
    rocket_speed: float = 12_800.0,
    dt: float = _cfg.ROCKET_DT,
    max_time: float = _cfg.ROCKET_MAX_TIME,        # ← longer window (was 1.0)
    thrust_dur: float = 2.0,
    drag_coefficient: float = _cfg.ROCKET_DRAG,
    wind: tuple[float, float, float] | None = None,
    mass_initial: float = _cfg.ROCKET_MASS_INITIAL,
    mass_dry: float = _cfg.ROCKET_MASS_DRY,
    mass_flow: float = _cfg.ROCKET_MASS_FLOW,
    gravity: float = 9.81,
) -> tuple[_F64Arr, _F64Arr, _F64Arr]:
    """
    Simple forward-fire rocket with constant thrust then ballistic coast.
    Vectorised – *plane_pos / plane_vel* may be (3,) or (N,3).
    """
    try:
        if any(v <= 0 for v in (dt, max_time, gravity)) or rocket_speed < 0:
            raise ValueError

        p0 = _as_batch(plane_pos)
        p0[:, 2] = np.maximum(p0[:, 2], 0.0)
        v_plane = _as_batch(plane_vel)

        v_mag = np.linalg.norm(v_plane, axis=1, keepdims=True)
        dir_vec = np.where(
            v_mag < 1e-6,
            np.array([[1.0, 0.0, 0.0]], dtype=np.float64),  # default forward
            v_plane / np.maximum(v_mag, 1e-6),
        )

        v0 = dir_vec * (v_mag + rocket_speed)
        if wind is None:
            wind = RUNTIME.environment.wind
        wind_vec = np.array(wind, dtype=np.float64)

        if drag_coefficient <= 0.0 and not np.any(wind_vec) and mass_flow <= 0.0:
            t_arr = np.arange(0.0, max_time + dt * 0.5, dt, dtype=np.float64)
            t_len = t_arr.size
            a_thrust = (t_arr < thrust_dur).astype(np.float64) * 15.0
            dv = np.cumsum(dir_vec[:, :, None] * a_thrust, axis=2) * dt
            v = v0[:, :, None] + dv
            v[:, 2, :] -= gravity * t_arr
            p = p0[:, :, None] + np.cumsum(v * dt, axis=2)
            impact = p[:, 2, :] <= 0.0
            hit = np.argmax(impact, axis=1)
            hit = np.where(impact.any(axis=1), hit, t_len)
            for i, h in enumerate(hit):
                if h < t_len:
                    p[i, 2, h:] = 0.0
                    p[i, 0, h:] = p[i, 0, h]
                    p[i, 1, h:] = p[i, 1, h]
            x, y, z = p[:, 0, :], p[:, 1, :], p[:, 2, :]
            return tuple(_unwrap_single(a) for a in (x, y, z))  # type: ignore[return-value]

        p = p0.copy()
        v = v0.copy()
        t_arr = np.arange(0.0, max_time + dt * 0.5, dt, dtype=np.float64)
        t_len = t_arr.size
        x = np.empty((p.shape[0], t_len), dtype=np.float64)
        y = np.empty_like(x)
        z = np.empty_like(x)
        x[:, 0], y[:, 0], z[:, 0] = p.T

        for k in range(1, t_len):
            t = float(t_arr[k])
            if t < thrust_dur:
                mass_scale = 1.0
                if mass_flow > 0.0 and mass_initial > 0.0 and mass_dry > 0.0:
                    mass = max(mass_dry, mass_initial - mass_flow * t)
                    if mass > 0.0:
                        mass_scale = mass_initial / mass
                v += dir_vec * (15.0 * mass_scale * dt)
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
            "simulate_rocket_trajectory",
            exc,
            {
                "dt": float(dt),
                "max_time": float(max_time),
                "rocket_speed": float(rocket_speed),
                "drag": float(drag_coefficient),
                "gravity": float(gravity),
                "mass_initial": float(mass_initial),
                "mass_dry": float(mass_dry),
                "mass_flow": float(mass_flow),
                "thrust_dur": float(thrust_dur),
            },
        )
        return _safe_empty()


# ───────────────────── scene-integration façade ──────────────────────────
_Launches: List[int] = []             # sorted queue of launch-frames
_LaunchIdx: int = 0
_RocketScatter: Any | None = None     # Path3DCollection created lazily
_ROCKET_COLORS = ("magenta", "cyan", "blue", "pink")
_ROCKET_EXPLOSION_SCALE = 0.6


def schedule_launch(frame_idx: int) -> None:
    """
    Queue a rocket launch for animation frame *frame_idx*.

    We keep the list **sorted** so that `step()` can simply look at the first
    element - no matter the order in which calls arrive.
    """
    bisect.insort(_Launches, int(frame_idx))


def reset() -> None:
    """Scene calls this once per loop-restart."""
    global _Launches, _LaunchIdx, _RocketScatter
    RUNTIME.active_rockets.clear()
    _Launches.clear()
    _LaunchIdx = 0
    if _RocketScatter is not None:
        try:
            _RocketScatter.remove()
        except Exception:
            pass
    _RocketScatter = None


def _spawn(
    frame: int,
    plane_pos: _Vec3,
    plane_vel: _Vec3,
    ax: Axes3D,
    *,
    dt: float,
) -> None:
    rx, ry, rz = simulate_rocket_trajectory(
        plane_pos,
        plane_vel,
        dt=dt,
    )
    RUNTIME.active_rockets.add(
        rx.astype(np.float32), ry.astype(np.float32), rz.astype(np.float32)
    )


def _update_all(frame: int, ax: Axes3D) -> None:
    global _RocketScatter
    xs, ys, zs, rows = RUNTIME.active_rockets.sample_positions()
    if rows.size == 0:
        if _RocketScatter is not None:
            _RocketScatter.set_visible(False)
        return
    ground = np.asarray(sample_height(xs, ys, default=0.0), dtype=np.float32)
    impact = zs <= ground
    if impact.any():
        from .explosions import spawn_explosion
        for x, y, z in zip(xs[impact], ys[impact], ground[impact]):
            spawn_explosion((float(x), float(y), float(z)), scale=_ROCKET_EXPLOSION_SCALE)
            RUNTIME.impacts.append(
                ImpactEvent(
                    frame=int(frame),
                    x=float(x),
                    y=float(y),
                    z=float(z),
                    target="terrain",
                    weapon="rocket",
                )
            )
        RUNTIME.active_rockets.remove(rows[impact])
        xs, ys, zs, rows = RUNTIME.active_rockets.sample_positions()
        if rows.size == 0:
            if _RocketScatter is not None:
                _RocketScatter.set_visible(False)
            return

    color = _ROCKET_COLORS[(frame // 5) % 4]
    ax_any = cast(Any, ax)
    if _RocketScatter is None:
        _RocketScatter = ax_any.scatter(
            xs,
            ys,
            zs,
            marker="^",
            s=40,
            color=color,
            depthshade=_cfg.SCATTER_DEPTHSHADE,
        )
    else:
        _RocketScatter._offsets3d = (xs, ys, zs)  # type: ignore[attr-defined]
        _RocketScatter.set_visible(True)
        _RocketScatter.set_color(color)
    RUNTIME.active_rockets.step()


def step(
    frame: int,
    plane_pos: _Vec3,
    plane_vel: _Vec3,
    ax: Axes3D,
    *,
    dt: float = _cfg.ROCKET_DT,
) -> None:
    """
    Advance rockets one animation tick:

    * Fire any rockets whose scheduled frame == *frame*.
    * Draw / update every in-flight rocket marker.
    """
    global _LaunchIdx, _Launches
    while _LaunchIdx < len(_Launches) and _Launches[_LaunchIdx] == frame:
        _LaunchIdx += 1
        _spawn(frame, plane_pos, plane_vel, ax, dt=dt)
    if _LaunchIdx > 32 and _LaunchIdx > (len(_Launches) // 2):
        _Launches = _Launches[_LaunchIdx:]
        _LaunchIdx = 0

    _update_all(frame, ax)
