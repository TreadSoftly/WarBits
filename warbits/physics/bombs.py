# pyright: reportMissingTypeStubs=false, reportUnknownMemberType=false
# ── warbits/physics/bombs.py ───────────────────────────────────────────────
from __future__ import annotations

from typing import Any, TYPE_CHECKING, Tuple, cast

import numpy as np
if TYPE_CHECKING:
    from matplotlib.axes import Axes
else:
    Axes = Any  # type: ignore[assignment]
from numpy.typing import NDArray

from ..config import settings as _cfg
from ..core.events import DebugEvent, ExplosionEvent, ImpactEvent
from ..logic.state import RUNTIME
from .terrain import sample_height

__all__ = [
    "simulate_bomb_trajectory",
    "schedule_release",
    "reset",
    "step",
]

# ─────────────────────────── type aliases ────────────────────────────────
_F64Arr     = NDArray[np.float64]
_VectorLike = Tuple[float, float, float] | NDArray[np.float64]
_Vec3       = Tuple[float, float, float]

# ─────────────────────────── private state ───────────────────────────────
_release_queue: list[int] = []          # frame indices when bombs drop
_scatter:    Any | None = None          # Path3DCollection created lazily
_BOMB_COLORS = ("white", "red", "yellow", "orange")
_BOMB_EXPLOSION_SCALE = 9.0


def _apply_bomb_blast(frame: int, x: float, y: float, z: float) -> None:
    try:
        from ..logic import enemy_ground as _ground
        from ..logic import enemy_bogies as _bogies
    except Exception:
        return
    _ground.apply_bomb_blast(frame, (x, y, z), scale=_BOMB_EXPLOSION_SCALE)
    _bogies.apply_bomb_blast(frame, (x, y, z), scale=_BOMB_EXPLOSION_SCALE)

# ─────────────────────── trajectory generator ────────────────────────────
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


def _as_batch(v: _VectorLike) -> NDArray[np.float64]:
    if isinstance(v, tuple):
        return np.asarray([v], dtype=np.float64)
    arr = np.asarray(v, dtype=np.float64)
    if arr.ndim != 2 or arr.shape[1] != 3:
        raise ValueError("vector must be shape (N,3)")
    return arr


def simulate_bomb_trajectory(
    start_pos: _VectorLike,
    start_vel: _VectorLike,
    *,
    dt: float = _cfg.BOMB_DT,
    max_time: float = _cfg.BOMB_MAX_TIME,
    drag_coefficient: float = _cfg.BOMB_DRAG,
    wind: Tuple[float, float, float] | None = None,
    gravity: float = 9.81,
) -> tuple[_F64Arr, _F64Arr, _F64Arr]:
    """Quad-drag + gravity unguided-bomb solver (vectorised)."""
    try:
        if any(v <= 0 for v in (dt, max_time, gravity)) or drag_coefficient < 0:
            raise ValueError

        p = _as_batch(start_pos)
        v = _as_batch(start_vel)
        if wind is None:
            wind = RUNTIME.environment.wind
        wind_vec = np.array(wind, dtype=np.float64)

        t = np.arange(0.0, max_time + dt * 0.5, dt, dtype=np.float64)
        T = t.size

        x = np.empty((p.shape[0], T), dtype=np.float64)
        y = np.empty_like(x)
        z = np.empty_like(x)
        x[:, 0], y[:, 0], z[:, 0] = p.T

        for k in range(1, T):
            rel = v - wind_vec
            speed = np.linalg.norm(rel, axis=1, keepdims=True)
            if drag_coefficient > 0.0:
                drag = drag_coefficient * speed**2
                v -= drag * rel / np.maximum(speed, 1e-6) * dt
            v[:, 2] -= gravity * dt

            p += v * dt
            impact = p[:, 2] <= 0.0
            p[impact, 2] = 0.0
            v[impact] = 0.0

            x[:, k], y[:, k], z[:, k] = p.T
            if impact.all():
                if k + 1 < T:
                    x[:, k + 1 :] = p[:, 0:1]
                    y[:, k + 1 :] = p[:, 1:2]
                    z[:, k + 1 :] = p[:, 2:3]
                break

        return tuple(_unwrap_single(a) for a in (x, y, z))  # type: ignore
    except Exception as exc:
        if _cfg.STRICT_PHYSICS:
            raise
        _log_physics_error(
            "simulate_bomb_trajectory",
            exc,
            {
                "dt": float(dt),
                "max_time": float(max_time),
                "drag": float(drag_coefficient),
                "gravity": float(gravity),
            },
        )
        return _safe_empty()

# ─────────────────────── scene-lifecycle hooks ───────────────────────────
def schedule_release(frame_idx: int) -> None:
    """Scene tells us once when the bomb should drop."""
    _release_queue.append(int(frame_idx))


def reset() -> None:
    """Scene calls once per loop-restart."""
    global _scatter
    _release_queue.clear()
    RUNTIME.active_bombs.clear()
    if _scatter is not None:
        try:
            _scatter.remove()
        except Exception:
            pass
    _scatter = None

# ───────────────────────── per-frame driver ──────────────────────────────
def step(
    frame: int,
    plane_pos: _Vec3,
    plane_vel: _Vec3,
    ax: Axes,
    *,
    dt: float = _cfg.BOMB_DT,
    drag_coefficient: float = _cfg.BOMB_DRAG,
    max_time: float = _cfg.BOMB_MAX_TIME,
) -> None:
    """
    Advance internal bomb state **once per animation frame**.
    """
    global _scatter

    # 1 ▸ Release
    if _release_queue:
        ready = [idx for idx in _release_queue if idx <= frame]
        if ready:
            _release_queue[:] = [idx for idx in _release_queue if idx > frame]
            sim_dt = max(float(_cfg.SIM_DT_MS) / 1000.0, 1e-6)
            dt_use = max(float(dt), 1e-6)
            vel_scale = sim_dt / dt_use
            vel_step = (
                plane_vel[0] * vel_scale,
                plane_vel[1] * vel_scale,
                plane_vel[2] * vel_scale,
            )
            for _ in ready:
                bx, by, bz = simulate_bomb_trajectory(
                    plane_pos,
                    vel_step,
                    dt=dt_use,
                    drag_coefficient=drag_coefficient,
                    max_time=max_time,
                )
                RUNTIME.active_bombs.add(
                    bx.astype(np.float32), by.astype(np.float32), bz.astype(np.float32)
                )

    # 2 ▸ In-flight / impact
    xs, ys, zs, rows = RUNTIME.active_bombs.sample_positions()
    if rows.size == 0:
        if _scatter is not None:
            _scatter.set_visible(False)
        return

    ground = np.asarray(sample_height(xs, ys, default=0.0), dtype=np.float32)
    impact = zs <= ground
    if impact.any():
        for x, y, z in zip(xs[impact], ys[impact], ground[impact]):
            from .explosions import spawn_explosion
            spawn_explosion(
                (float(x), float(y), float(z)),
                scale=_BOMB_EXPLOSION_SCALE,
                style="mushroom",
            )
            RUNTIME.explosions.append(
                ExplosionEvent(
                    frame=int(frame),
                    x=float(x),
                    y=float(y),
                    z=float(z),
                    scale=_BOMB_EXPLOSION_SCALE,
                    style="mushroom",
                )
            )
            RUNTIME.impacts.append(
                ImpactEvent(
                    frame=int(frame),
                    x=float(x),
                    y=float(y),
                    z=float(z),
                    target="terrain",
                    weapon="bomb",
                )
            )
            _apply_bomb_blast(frame, float(x), float(y), float(z))
        RUNTIME.active_bombs.remove(rows[impact])
        xs, ys, zs, rows = RUNTIME.active_bombs.sample_positions()
        if rows.size == 0:
            if _scatter is not None:
                _scatter.remove()
            _scatter = None
            return
        ground = np.asarray(sample_height(xs, ys, default=0.0), dtype=np.float32)

    lengths = RUNTIME.active_bombs.lengths
    indices = RUNTIME.active_bombs.sample_index
    if lengths.size and indices.size and lengths.shape == indices.shape:
        end_mask = indices >= (lengths - 1)
        if end_mask.any():
            for x, y, z in zip(xs[end_mask], ys[end_mask], ground[end_mask]):
                from .explosions import spawn_explosion
                spawn_explosion(
                    (float(x), float(y), float(z)),
                    scale=_BOMB_EXPLOSION_SCALE,
                    style="mushroom",
                )
                RUNTIME.explosions.append(
                    ExplosionEvent(
                        frame=int(frame),
                        x=float(x),
                        y=float(y),
                        z=float(z),
                        scale=_BOMB_EXPLOSION_SCALE,
                        style="mushroom",
                    )
                )
                RUNTIME.impacts.append(
                    ImpactEvent(
                        frame=int(frame),
                        x=float(x),
                        y=float(y),
                        z=float(z),
                        target="terrain",
                        weapon="bomb",
                    )
                )
                _apply_bomb_blast(frame, float(x), float(y), float(z))
            RUNTIME.active_bombs.remove(rows[end_mask])
            xs, ys, zs, rows = RUNTIME.active_bombs.sample_positions()
            if rows.size == 0:
                if _scatter is not None:
                    _scatter.remove()
                _scatter = None
                return
            ground = np.asarray(sample_height(xs, ys, default=0.0), dtype=np.float32)

    ax_any = cast(Any, ax)
    if _scatter is None:
        _scatter = ax_any.scatter(
            xs,
            ys,
            zs,
            s=50,
            color="white",
            depthshade=_cfg.SCATTER_DEPTHSHADE,
        )
    else:
        _scatter._offsets3d = (xs, ys, zs)  # type: ignore[attr-defined]

    blink = max(1, 10 - int(max(float(np.max(zs)), 0.0) / 100.0))
    if _scatter is not None:
        _scatter.set_color(_BOMB_COLORS[(frame // blink) % 4])
        _scatter.set_visible(True)
    RUNTIME.active_bombs.step()
