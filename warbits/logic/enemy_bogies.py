# ── warbits/logic/enemy_bogies.py ───────────────────────────────────────────
# pyright: reportUnusedImport=false, reportUnusedVariable=false, reportUnusedFunction=false
from __future__ import annotations
# Bogie AI, damage logic, parachute bail-out & mesh handling
# ---------------------------------------------------------------------------
import math
from typing import Any, Dict, Tuple

import numpy as np
import numpy.typing as npt
from mpl_toolkits.mplot3d import Axes3D                 # type: ignore
from mpl_toolkits.mplot3d.art3d import Poly3DCollection # type: ignore

from .aircraft import BOGIE_SCALE, create_bogie_model, update_mesh
from ..config import settings as _cfg
from ..core.events import ImpactEvent
from ..logic.state import RUNTIME
from ..physics.explosions import spawn_explosion
from ..physics.parachute  import spawn_parachute
from ..physics.terrain import sample_height

__all__ = [
    "init",
    "reset",
    "update",
    "update_bogie",
    "configure",
    "set_flight_path",
    "get_position",
    "is_alive",
    "apply_bomb_blast",
]

NDArrayF = npt.NDArray[np.float64]
_F32Arr = npt.NDArray[np.float32]

# ---------------------------------------------------------------------------
# Runtime state
# ---------------------------------------------------------------------------
_ax: Axes3D | None = None

_fx: NDArrayF | None = None
_fy: NDArrayF | None = None
_fz: NDArrayF | None = None
_slice_map: Dict[str, Tuple[int, int]] | None = None
_n_frames: int = 0

_bog_x: NDArrayF | None = None
_bog_y: NDArrayF | None = None
_bog_z: NDArrayF | None = None

_bogie: Poly3DCollection | None = None
_bogie_glow: Any | None = None
_bogie_hit: bool = False
_bogie_hit_at: int | None = None
_bogie_hit_tick: int | None = None
_bogie_hit_origin: Tuple[float, float, float] | None = None
_bogie_fall_prev: Tuple[float, float, float] | None = None
_parachute_deployed: bool = False
_bogie_destroyed: bool = False
_bogie_hp: float = 1.0
_bogie_damaged: bool = False
_hit_frame_override: int | None = None
_bogie_spawned: bool = False
_bogie_appear_at: int | None = None
_bogie_vel: Tuple[float, float, float] | None = None
_bogie_weave_phase = 0.0
_bogie_pos: Tuple[float, float, float] | None = None
_bogie_mode: str | None = None
_bogie_closing_factor: float | None = None
_bogie_target_sep: float | None = None
_bogie_prev_pos: Tuple[float, float, float] | None = None
_bogie_last_frame: int | None = None
_bogie_repeat_count = 0
_bogie_stall_count = 0

# initial spawn
_BX0, _BY0, _BZ0 = 20_000.0, 7_500.0, 500.0
_CLOSING_FACTOR  = 0.20
_SEPARATION_DISTANCE = 1_050.0
_SPAWN_MARGIN = 2_000.0
_BOGIE_TERRAIN_CLEARANCE = 250.0
_BOGIE_HIT_RADIUS_BULLET = 220.0
_BOGIE_HIT_RADIUS_ROCKET = 320.0
_BOGIE_HIT_RADIUS_BOMB = 380.0
_BOGIE_HIT_RADIUS_BULLET_SQ = _BOGIE_HIT_RADIUS_BULLET * _BOGIE_HIT_RADIUS_BULLET
_BOGIE_HIT_RADIUS_ROCKET_SQ = _BOGIE_HIT_RADIUS_ROCKET * _BOGIE_HIT_RADIUS_ROCKET
_BOGIE_HIT_RADIUS_BOMB_SQ = _BOGIE_HIT_RADIUS_BOMB * _BOGIE_HIT_RADIUS_BOMB
_BOGIE_HIT_EXPLOSION_SCALE = 0.6
_BOGIE_BLAST_KILL_RADIUS = 520.0
_BOGIE_BLAST_DAMAGE_RADIUS = 1150.0
_BOGIE_BLAST_DAMAGE_SCALE = 0.7
_BOGIE_BLAST_MIN_DAMAGE = 0.15
_BOGIE_BLAST_SCALE_REF = 9.0
_BOGIE_DAMAGE_SPEED_SCALE = 0.86
_BOGIE_FALL_SPEED = 200.0
_BOGIE_FALL_GRAVITY = 900.0
_BOGIE_FALL_MAX_SECONDS = 8.0
_BOGIE_GLOW_SIZE = 120.0
_BOGIE_DOGFIGHT_SPEED = 320.0
_BOGIE_DOGFIGHT_LEAD = 1.8
_BOGIE_DOGFIGHT_TURN = 0.14
_BOGIE_DOGFIGHT_LATERAL = 700.0
_BOGIE_DOGFIGHT_WEAVE = 300.0
_BOGIE_DOGFIGHT_WEAVE_RATE = 0.9
_BOGIE_DOGFIGHT_ALT_BIAS = 140.0
_BOGIE_DOGFIGHT_ALT_WEAVE = 70.0
_BOGIE_DOGFIGHT_MIN_SEP = 650.0
_BOGIE_DOGFIGHT_MAX_SEP = 7000.0
_BOGIE_APPROACH_SPEED = 380.0
_BOGIE_APPROACH_TURN = 0.10
_BOGIE_APPROACH_RANGE = _BOGIE_DOGFIGHT_MAX_SEP * 0.85
_BOGIE_REPEAT_MOVE_INTERVAL = 1
_BOGIE_STALL_RESET_FRAMES = 24
_BOGIE_STALL_EPS = 2.0
# ---------------------------------------------------------------------------
# Initialise once
# ---------------------------------------------------------------------------
def init(
    ax: Axes3D,
    flight_x: NDArrayF,
    flight_y: NDArrayF,
    flight_z: NDArrayF,
    slice_map: Dict[str, Tuple[int, int]],
    *,
    appear_at: int | None = None,
    closing_factor: float | None = None,
    hit_frame: int | None = None,
) -> None:
    global _ax
    _ax = ax
    set_flight_path(flight_x, flight_y, flight_z, slice_map)

    configure(
        appear_at=appear_at,
        closing_factor=closing_factor,
        hit_frame=hit_frame,
    )


def set_flight_path(
    flight_x: NDArrayF,
    flight_y: NDArrayF,
    flight_z: NDArrayF,
    slice_map: Dict[str, Tuple[int, int]],
) -> None:
    global _fx, _fy, _fz, _slice_map, _n_frames
    global _bog_x, _bog_y, _bog_z
    _fx, _fy, _fz = flight_x, flight_y, flight_z
    _slice_map = slice_map
    _n_frames = int(flight_x.shape[0])

    _bog_x = np.full(_n_frames, np.nan)
    _bog_y = np.full_like(_bog_x, np.nan)
    _bog_z = np.full_like(_bog_x, np.nan)


def get_position(frame: int) -> Tuple[float, float, float] | None:
    if _bogie_hit or _bogie_destroyed:
        return None
    if _bogie_pos is not None:
        return _bogie_pos
    if _bog_x is None or _bog_y is None or _bog_z is None:
        return None
    if frame < 0 or frame >= _n_frames:
        if _bogie_pos is not None:
            return _bogie_pos
        return None
    bx = _bog_x[frame]
    by = _bog_y[frame]
    bz = _bog_z[frame]
    if not (np.isnan(bx) or np.isnan(by) or np.isnan(bz)):
        return float(bx), float(by), float(bz)
    if _bogie_pos is not None:
        return _bogie_pos
    return None


def is_alive() -> bool:
    """Return True while the bogie has not been destroyed."""
    return (not _bogie_destroyed) and _bogie_spawned and (not _bogie_hit)


def _segment_any_hit(
    paths: _F32Arr,
    sample_index: npt.NDArray[np.int32],
    bx: float,
    by: float,
    bz: float,
    radius_sq: float,
) -> bool:
    if paths.size == 0:
        return False
    n = int(paths.shape[0])
    if n == 0 or paths.shape[2] == 0:
        return False
    idx = np.clip(sample_index.astype(np.int64), 0, paths.shape[2] - 1)
    idx0 = np.maximum(idx - 1, 0)
    idx_expand = np.broadcast_to(idx[:, None, None], (n, 3, 1))
    idx0_expand = np.broadcast_to(idx0[:, None, None], (n, 3, 1))
    p1 = np.take_along_axis(paths, idx_expand, axis=2)[:, :, 0]
    p0 = np.take_along_axis(paths, idx0_expand, axis=2)[:, :, 0]
    v = p1 - p0
    w = np.array([bx, by, bz], dtype=np.float32) - p0
    v_len_sq = np.sum(v * v, axis=1)
    dot = np.sum(w * v, axis=1)
    t = np.zeros_like(dot, dtype=np.float32)
    np.divide(dot, v_len_sq, out=t, where=v_len_sq > 1e-9)
    t = np.clip(t, 0.0, 1.0)
    closest = p0 + v * t[:, None]
    dx = closest[:, 0] - bx
    dy = closest[:, 1] - by
    dz = closest[:, 2] - bz
    return bool(np.any(dx * dx + dy * dy + dz * dz <= radius_sq))


def _check_projectile_hit(bx: float, by: float, bz: float) -> str | None:
    paths = RUNTIME.active_bullets.paths
    idx = RUNTIME.active_bullets.sample_index
    if _segment_any_hit(paths, idx, bx, by, bz, _BOGIE_HIT_RADIUS_BULLET_SQ):
        return "bullet"
    paths = RUNTIME.active_rockets.paths
    idx = RUNTIME.active_rockets.sample_index
    if _segment_any_hit(paths, idx, bx, by, bz, _BOGIE_HIT_RADIUS_ROCKET_SQ):
        return "rocket"
    paths = RUNTIME.active_bombs.paths
    idx = RUNTIME.active_bombs.sample_index
    if _segment_any_hit(paths, idx, bx, by, bz, _BOGIE_HIT_RADIUS_BOMB_SQ):
        return "bomb"
    return None


def _record_impact(
    frame: int,
    x: float,
    y: float,
    z: float,
    *,
    target: str,
    weapon: str,
) -> None:
    RUNTIME.impacts.append(
        ImpactEvent(
            frame=int(frame),
            x=float(x),
            y=float(y),
            z=float(z),
            target=target,
            weapon=weapon,
        )
    )

def _scene_span_xy() -> float:
    span_x = float(_cfg.TERRAIN_XMAX - _cfg.TERRAIN_XMIN)
    span_y = float(_cfg.TERRAIN_YMAX - _cfg.TERRAIN_YMIN)
    if not (math.isfinite(span_x) and math.isfinite(span_y)):
        return 1.0
    return max(1.0, min(span_x, span_y))


def _dogfight_step(frame: int, bx: float, by: float, bz: float) -> Tuple[float, float, float]:
    plane_pos = RUNTIME.flight.plane_pos
    plane_vel = RUNTIME.flight.plane_vel
    px, py, pz = plane_pos
    vx, vy, vz = plane_vel
    if not (math.isfinite(px) and math.isfinite(py) and math.isfinite(pz)):
        px, py, pz = bx, by, bz
    if not (math.isfinite(vx) and math.isfinite(vy) and math.isfinite(vz)):
        vx, vy, vz = 0.0, 0.0, 0.0
    if not (np.isfinite(bx) and np.isfinite(by) and np.isfinite(bz)):
        bx, by, bz = px, py, pz
    speed_xy = math.hypot(vx, vy)
    if speed_xy < 1.0e-3:
        dir_x, dir_y = _bogie_heading(bx, by)
    else:
        dir_x, dir_y = vx / speed_xy, vy / speed_xy
    side_x, side_y = -dir_y, dir_x

    dt = max(_cfg.SIM_DT_MS / 1000.0, 1e-6)
    span_xy = _scene_span_xy()
    global _bogie_weave_phase, _bogie_vel
    _bogie_weave_phase += _BOGIE_DOGFIGHT_WEAVE_RATE * dt
    weave = math.sin(_bogie_weave_phase)
    lateral_base = max(_BOGIE_DOGFIGHT_LATERAL, span_xy * 0.01)
    weave_amp = max(_BOGIE_DOGFIGHT_WEAVE, lateral_base * 0.4)
    lateral = lateral_base + (weave_amp * weave)

    lead = _BOGIE_DOGFIGHT_LEAD
    dist_plane = math.hypot(bx - px, by - py)
    if dist_plane > _BOGIE_DOGFIGHT_MAX_SEP:
        lead = 0.8
        lateral = 0.0
    elif dist_plane < (_BOGIE_DOGFIGHT_MIN_SEP * 1.4):
        lateral *= max(0.35, dist_plane / (_BOGIE_DOGFIGHT_MIN_SEP * 1.4))
        lateral = max(lateral, lateral_base * 0.25)

    target_x = px + vx * lead + side_x * lateral
    target_y = py + vy * lead + side_y * lateral
    target_z = pz + _BOGIE_DOGFIGHT_ALT_BIAS + math.cos(_bogie_weave_phase * 0.7) * _BOGIE_DOGFIGHT_ALT_WEAVE

    if dist_plane < _BOGIE_DOGFIGHT_MIN_SEP and dist_plane > 1e-3:
        push = (_BOGIE_DOGFIGHT_MIN_SEP - dist_plane) / _BOGIE_DOGFIGHT_MIN_SEP
        target_x += ((bx - px) / dist_plane) * (800.0 * push)
        target_y += ((by - py) / dist_plane) * (800.0 * push)

    min_x = float(_cfg.TERRAIN_XMIN)
    max_x = float(_cfg.TERRAIN_XMAX)
    min_y = float(_cfg.TERRAIN_YMIN)
    max_y = float(_cfg.TERRAIN_YMAX)
    target_x = min(max(target_x, min_x), max_x)
    target_y = min(max(target_y, min_y), max_y)

    dx = target_x - bx
    dy = target_y - by
    dz = target_z - bz
    dist = math.sqrt(dx * dx + dy * dy + dz * dz)
    if dist < 1.0e-3 or not math.isfinite(dist):
        _bogie_vel = None
        min_step = max(_BOGIE_STALL_EPS * 2.5, span_xy * 0.0005)
        step = max(_BOGIE_DOGFIGHT_SPEED * dt, min_step)
        if _bogie_prev_pos is not None:
            hx, hy = _normalize_xy(bx - _bogie_prev_pos[0], by - _bogie_prev_pos[1])
        else:
            hx, hy = dir_x, dir_y
        side_x, side_y = -hy, hx
        nx = bx + (hx * step) + (side_x * (lateral_base * 0.15))
        ny = by + (hy * step) + (side_y * (lateral_base * 0.15))
        nz = bz + _BOGIE_DOGFIGHT_ALT_BIAS * 0.05
        nx = min(max(nx, min_x), max_x)
        ny = min(max(ny, min_y), max_y)
        ground_z = float(sample_height(nx, ny, default=_cfg.TERRAIN_ZMIN))
        min_z = ground_z + _BOGIE_TERRAIN_CLEARANCE
        if nz < min_z:
            nz = min_z
        return nx, ny, nz
    plane_speed = math.sqrt(vx * vx + vy * vy + vz * vz)
    speed = _BOGIE_DOGFIGHT_SPEED
    if plane_speed > 1.0e-3:
        speed = max(_BOGIE_DOGFIGHT_SPEED, plane_speed * 1.05)
    if _bogie_damaged:
        speed *= _BOGIE_DAMAGE_SPEED_SCALE
    scale = speed / dist
    desired = (dx * scale, dy * scale, dz * scale)
    if _bogie_vel is not None and (not math.isfinite(_bogie_vel[0]) or not math.isfinite(_bogie_vel[1]) or not math.isfinite(_bogie_vel[2])):
        _bogie_vel = None
    if _bogie_vel is not None and (not math.isfinite(_bogie_vel[0]) or not math.isfinite(_bogie_vel[1]) or not math.isfinite(_bogie_vel[2])):
        _bogie_vel = None
    if _bogie_vel is None:
        _bogie_vel = desired
    else:
        _bogie_vel = (
            _bogie_vel[0] + (desired[0] - _bogie_vel[0]) * _BOGIE_DOGFIGHT_TURN,
            _bogie_vel[1] + (desired[1] - _bogie_vel[1]) * _BOGIE_DOGFIGHT_TURN,
            _bogie_vel[2] + (desired[2] - _bogie_vel[2]) * _BOGIE_DOGFIGHT_TURN,
        )
    nx = bx + _bogie_vel[0] * dt
    ny = by + _bogie_vel[1] * dt
    nz = bz + _bogie_vel[2] * dt
    if not (math.isfinite(nx) and math.isfinite(ny) and math.isfinite(nz)):
        return bx, by, bz
    nx = min(max(nx, min_x), max_x)
    ny = min(max(ny, min_y), max_y)
    ground_z = float(sample_height(nx, ny, default=_cfg.TERRAIN_ZMIN))
    min_z = ground_z + _BOGIE_TERRAIN_CLEARANCE
    if nz < min_z:
        nz = min_z
    return nx, ny, nz


def _approach_step(frame: int, bx: float, by: float, bz: float) -> Tuple[float, float, float, bool]:
    plane_pos = RUNTIME.flight.plane_pos
    plane_vel = RUNTIME.flight.plane_vel
    px, py, pz = plane_pos
    vx, vy, vz = plane_vel
    if not (math.isfinite(px) and math.isfinite(py) and math.isfinite(pz)):
        px, py, pz = bx, by, bz
    if not (math.isfinite(vx) and math.isfinite(vy) and math.isfinite(vz)):
        vx, vy, vz = 0.0, 0.0, 0.0
    speed_xy = math.hypot(vx, vy)
    if speed_xy < 1.0e-3:
        dxp = px - bx
        dyp = py - by
        if abs(dxp) + abs(dyp) > 1.0e-6:
            dir_x, dir_y = _normalize_xy(dxp, dyp)
        else:
            dir_x, dir_y = _bogie_heading(bx, by)
    else:
        dir_x, dir_y = vx / speed_xy, vy / speed_xy
    side_x, side_y = -dir_y, dir_x
    lead = _BOGIE_DOGFIGHT_LEAD * 0.6
    offset = (_bogie_target_sep or _SEPARATION_DISTANCE) * 0.2
    target_x = px + vx * lead + side_x * offset
    target_y = py + vy * lead + side_y * offset
    target_z = pz + _BOGIE_DOGFIGHT_ALT_BIAS * 0.6

    min_x = float(_cfg.TERRAIN_XMIN)
    max_x = float(_cfg.TERRAIN_XMAX)
    min_y = float(_cfg.TERRAIN_YMIN)
    max_y = float(_cfg.TERRAIN_YMAX)
    target_x = min(max(target_x, min_x), max_x)
    target_y = min(max(target_y, min_y), max_y)

    dx = target_x - bx
    dy = target_y - by
    dz = target_z - bz
    dist = math.sqrt(dx * dx + dy * dy + dz * dz)
    if dist < 1.0e-3 or not math.isfinite(dist):
        return bx, by, bz, True

    speed_scale = 1.0
    if _bogie_closing_factor is not None and _CLOSING_FACTOR > 0.0:
        speed_scale = max(0.6, min(1.6, _bogie_closing_factor / _CLOSING_FACTOR))
    plane_speed = math.sqrt(vx * vx + vy * vy + vz * vz)
    speed = max(_BOGIE_APPROACH_SPEED, plane_speed * 1.10) * speed_scale
    if _bogie_damaged:
        speed *= _BOGIE_DAMAGE_SPEED_SCALE
    scale = speed / dist
    desired = (dx * scale, dy * scale, dz * scale)
    global _bogie_vel
    if _bogie_vel is not None and (not math.isfinite(_bogie_vel[0]) or not math.isfinite(_bogie_vel[1]) or not math.isfinite(_bogie_vel[2])):
        _bogie_vel = None
    if _bogie_vel is None:
        _bogie_vel = desired
    else:
        _bogie_vel = (
            _bogie_vel[0] + (desired[0] - _bogie_vel[0]) * _BOGIE_APPROACH_TURN,
            _bogie_vel[1] + (desired[1] - _bogie_vel[1]) * _BOGIE_APPROACH_TURN,
            _bogie_vel[2] + (desired[2] - _bogie_vel[2]) * _BOGIE_APPROACH_TURN,
        )
    dt = max(_cfg.SIM_DT_MS / 1000.0, 1e-6)
    nx = bx + _bogie_vel[0] * dt
    ny = by + _bogie_vel[1] * dt
    nz = bz + _bogie_vel[2] * dt
    if not (math.isfinite(nx) and math.isfinite(ny) and math.isfinite(nz)):
        return bx, by, bz, False
    nx = min(max(nx, min_x), max_x)
    ny = min(max(ny, min_y), max_y)
    ground_z = float(sample_height(nx, ny, default=_cfg.TERRAIN_ZMIN))
    min_z = ground_z + _BOGIE_TERRAIN_CLEARANCE
    if nz < min_z:
        nz = min_z
    dist_plane = math.hypot(bx - px, by - py)
    reached = dist_plane <= _BOGIE_APPROACH_RANGE
    return nx, ny, nz, reached


def _normalize_xy(dx: float, dy: float) -> Tuple[float, float]:
    dist = math.hypot(dx, dy)
    if dist < 1.0e-6:
        return 1.0, 0.0
    return dx / dist, dy / dist


def _bogie_heading(bx: float, by: float) -> Tuple[float, float]:
    """Fallback heading when the player aircraft has near-zero velocity."""
    if _bogie_vel is not None:
        vx, vy = _bogie_vel[0], _bogie_vel[1]
        if math.isfinite(vx) and math.isfinite(vy) and (abs(vx) + abs(vy) > 1.0e-3):
            return _normalize_xy(vx, vy)
    if _bogie_prev_pos is not None:
        dx = bx - _bogie_prev_pos[0]
        dy = by - _bogie_prev_pos[1]
        if math.isfinite(dx) and math.isfinite(dy) and (abs(dx) + abs(dy) > 1.0e-6):
            return _normalize_xy(dx, dy)
    return 1.0, 0.0


def _compute_spawn_pos(
    px: float,
    py: float,
    pz: float,
    heading_x: float,
    heading_y: float,
) -> Tuple[float, float, float]:
    target_sep = _bogie_target_sep or _SEPARATION_DISTANCE
    spawn_dist = max(target_sep * 1.35, _SPAWN_MARGIN * 1.2)
    spawn_x = px + heading_x * spawn_dist
    spawn_y = py + heading_y * spawn_dist
    min_x = float(_cfg.TERRAIN_XMIN)
    max_x = float(_cfg.TERRAIN_XMAX)
    min_y = float(_cfg.TERRAIN_YMIN)
    max_y = float(_cfg.TERRAIN_YMAX)
    if min_x <= spawn_x <= max_x:
        spawn_x = (max_x + _SPAWN_MARGIN) if heading_x >= 0.0 else (min_x - _SPAWN_MARGIN)
    if min_y <= spawn_y <= max_y:
        spawn_y = (max_y + _SPAWN_MARGIN) if heading_y >= 0.0 else (min_y - _SPAWN_MARGIN)
    ground_z = float(sample_height(spawn_x, spawn_y, default=pz))
    spawn_z = max(pz + _BOGIE_DOGFIGHT_ALT_BIAS * 0.4, ground_z + _BOGIE_TERRAIN_CLEARANCE)
    return spawn_x, spawn_y, spawn_z


def _unstick_bogie(
    frame: int,
    bx: float,
    by: float,
    bz: float,
) -> Tuple[float, float, float]:
    plane_pos = RUNTIME.flight.plane_pos
    plane_vel = RUNTIME.flight.plane_vel
    px, py, pz = plane_pos
    vx, vy, _ = plane_vel
    if not (math.isfinite(px) and math.isfinite(py) and math.isfinite(pz)):
        px, py, pz = bx, by, bz
    if not (math.isfinite(vx) and math.isfinite(vy)):
        heading_x, heading_y = _bogie_heading(bx, by)
    else:
        speed_xy = math.hypot(vx, vy)
        if speed_xy < 1.0e-3:
            heading_x, heading_y = _bogie_heading(bx, by)
        else:
            heading_x, heading_y = vx / speed_xy, vy / speed_xy
    side_x, side_y = -heading_y, heading_x
    span_xy = _scene_span_xy()
    spawn_dist = max(_BOGIE_DOGFIGHT_MIN_SEP * 1.2, _SPAWN_MARGIN * 0.6, span_xy * 0.012)
    lateral = max(_BOGIE_DOGFIGHT_LATERAL * 0.5, span_xy * 0.004)
    nx = px + heading_x * spawn_dist + side_x * lateral
    ny = py + heading_y * spawn_dist + side_y * lateral
    min_x = float(_cfg.TERRAIN_XMIN)
    max_x = float(_cfg.TERRAIN_XMAX)
    min_y = float(_cfg.TERRAIN_YMIN)
    max_y = float(_cfg.TERRAIN_YMAX)
    nx = min(max(nx, min_x), max_x)
    ny = min(max(ny, min_y), max_y)
    # Ensure the unstick move actually changes position even when clamped.
    dx = nx - bx
    dy = ny - by
    min_move = max(_BOGIE_STALL_EPS * 2.5, span_xy * 0.002)
    min_move_sq = min_move * min_move
    if (dx * dx + dy * dy) < min_move_sq:
        best_x, best_y = nx, ny
        best_d2 = dx * dx + dy * dy
        candidates = (
            (heading_x, heading_y),
            (-heading_x, -heading_y),
            (side_x, side_y),
            (-side_x, -side_y),
        )
        for hx, hy in candidates:
            sx, sy = -hy, hx
            tx = px + hx * spawn_dist + sx * lateral
            ty = py + hy * spawn_dist + sy * lateral
            tx = min(max(tx, min_x), max_x)
            ty = min(max(ty, min_y), max_y)
            d2 = (tx - bx) * (tx - bx) + (ty - by) * (ty - by)
            if d2 > best_d2:
                best_d2, best_x, best_y = d2, tx, ty
        if best_d2 < min_move_sq:
            nudge_x = min_move if (max_x - bx) >= (bx - min_x) else -min_move
            tx = min(max(bx + nudge_x, min_x), max_x)
            d2 = (tx - bx) * (tx - bx) + (best_y - by) * (best_y - by)
            if d2 > best_d2:
                best_d2, best_x, best_y = d2, tx, best_y
            nudge_y = min_move if (max_y - by) >= (by - min_y) else -min_move
            ty = min(max(by + nudge_y, min_y), max_y)
            d2 = (best_x - bx) * (best_x - bx) + (ty - by) * (ty - by)
            if d2 > best_d2:
                best_d2, best_x, best_y = d2, best_x, ty
        nx, ny = best_x, best_y
    ground_z = float(sample_height(nx, ny, default=_cfg.TERRAIN_ZMIN))
    nz = max(pz + _BOGIE_DOGFIGHT_ALT_BIAS * 0.6, ground_z + _BOGIE_TERRAIN_CLEARANCE)
    bog_x = _bog_x
    bog_y = _bog_y
    bog_z = _bog_z
    if bog_x is None or bog_y is None or bog_z is None:
        return nx, ny, nz
    if frame < bog_x.size:
        bog_x[frame], bog_y[frame], bog_z[frame] = nx, ny, nz
    return nx, ny, nz

# ---------------------------------------------------------------------------
# Reset per loop
# ---------------------------------------------------------------------------
def reset() -> None:
    global _bogie, _bogie_glow, _bogie_hit, _bogie_hit_at, _bogie_hit_tick, _bogie_hit_origin, _bogie_fall_prev
    global _parachute_deployed, _bogie_destroyed
    global _bogie_hp, _bogie_damaged
    global _hit_frame_override, _bogie_spawned, _bogie_appear_at, _bogie_vel, _bogie_weave_phase
    global _bogie_mode, _bogie_closing_factor, _bogie_target_sep, _bogie_prev_pos
    global _bogie_last_frame, _bogie_repeat_count, _bogie_stall_count
    global _bogie_pos
    _bogie_hit          = False
    _bogie_hit_at       = None
    _bogie_hit_tick     = None
    _bogie_hit_origin   = None
    _bogie_fall_prev    = None
    _parachute_deployed = False
    _bogie_destroyed    = False
    _bogie_hp = 1.0
    _bogie_damaged = False
    _hit_frame_override = None
    _bogie_spawned = False
    _bogie_appear_at = None
    _bogie_vel = None
    _bogie_weave_phase = 0.0
    _bogie_pos = None
    _bogie_mode = None
    _bogie_closing_factor = None
    _bogie_target_sep = None
    _bogie_prev_pos = None
    _bogie_last_frame = None
    _bogie_repeat_count = 0
    _bogie_stall_count = 0
    if _bogie is not None:
        try:
            _bogie.remove()
        except Exception:
            pass
    _bogie = None
    if _bogie_glow is not None:
        try:
            _bogie_glow.remove()
        except Exception:
            pass
    _bogie_glow = None


def _update_glow(bx: float, by: float, bz: float) -> None:
    global _bogie_glow
    if _ax is None:
        return
    ax_any: Any = _ax
    color = "#ff6b6b" if not _bogie_damaged else "#ffb347"
    if _bogie_glow is None:
        _bogie_glow = ax_any.scatter(
            bx,
            by,
            bz,
            s=float(_BOGIE_GLOW_SIZE),
            c=color,
            alpha=0.85,
            depthshade=False,
        )
    else:
        try:
            _bogie_glow._offsets3d = ([bx], [by], [bz])
            _bogie_glow.set_color(color)
        except Exception:
            pass

# ---------------------------------------------------------------------------
# Optional external tweak
# ---------------------------------------------------------------------------
def update_bogie(
    target_pos: Tuple[float, float, float],
    closing_factor: float = 0.20,
) -> None:
    if _bog_x is None or _bog_y is None or _bog_z is None:
        return
    bx, by, bz = _bog_x[0], _bog_y[0], _bog_z[0]
    tx, ty, tz = target_pos
    _bog_x[0] = bx + closing_factor * (tx - bx)
    _bog_y[0] = by + closing_factor * (ty - by)
    _bog_z[0] = bz + closing_factor * (tz - bz)

# ---------------------------------------------------------------------------
# Scenario overrides
# ---------------------------------------------------------------------------
def configure(
    *,
    appear_at: int | None = None,
    closing_factor: float | None = None,
    hit_frame: int | None = None,
    separation: float | None = None,
) -> None:
    global _bog_x, _bog_y, _bog_z, _hit_frame_override, _bogie_spawned, _bogie_appear_at
    global _bogie_closing_factor, _bogie_target_sep, _bogie_mode, _bogie_pos, _bogie_vel, _bogie_weave_phase
    global _bogie_prev_pos, _bogie_last_frame, _bogie_repeat_count, _bogie_stall_count, _bogie_hp, _bogie_damaged
    if _fx is None or _fy is None or _fz is None or _slice_map is None:
        return
    if _bog_x is None or _bog_y is None or _bog_z is None:
        return

    if appear_at is None:
        escape = _slice_map.get("Escape")
        if escape is not None:
            appear_at = escape[1] - 20
        else:
            appear_at = _n_frames - 20
    appear_at = max(0, min(int(appear_at), _n_frames - 1))
    _bogie_appear_at = appear_at
    _bogie_spawned = False
    _bogie_closing_factor = _CLOSING_FACTOR if closing_factor is None else float(closing_factor)
    _bogie_target_sep = _SEPARATION_DISTANCE if separation is None else float(separation)
    _bogie_pos = None
    _bogie_vel = None
    _bogie_weave_phase = 0.0
    _bogie_mode = None
    _bogie_prev_pos = None
    _bogie_last_frame = None
    _bogie_repeat_count = 0
    _bogie_stall_count = 0
    _bogie_hp = 1.0
    _bogie_damaged = False

    _bog_x.fill(np.nan)
    _bog_y.fill(np.nan)
    _bog_z.fill(np.nan)

    if _n_frames > 0 and 0 <= appear_at < _n_frames:
        px = float(_fx[appear_at])
        py = float(_fy[appear_at])
        pz = float(_fz[appear_at])
        if appear_at > 0:
            dx = float(_fx[appear_at]) - float(_fx[appear_at - 1])
            dy = float(_fy[appear_at]) - float(_fy[appear_at - 1])
        else:
            dx, dy = 1.0, 0.0
        heading_x, heading_y = _normalize_xy(dx, dy)
        spawn_x, spawn_y, spawn_z = _compute_spawn_pos(px, py, pz, heading_x, heading_y)
        _bog_x[appear_at], _bog_y[appear_at], _bog_z[appear_at] = spawn_x, spawn_y, spawn_z

    if hit_frame is not None:
        hit_frame = int(hit_frame)
        if hit_frame < appear_at:
            hit_frame = min(appear_at + 20, _n_frames - 1)
        if hit_frame >= _n_frames:
            hit_frame = None
    _hit_frame_override = hit_frame

# ---------------------------------------------------------------------------
# Per-frame update
# ---------------------------------------------------------------------------
def update(frame: int) -> None:
    global _bogie, _bogie_glow, _bogie_hit, _bogie_hit_at, _bogie_hit_tick, _bogie_hit_origin, _bogie_fall_prev
    global _parachute_deployed, _bogie_destroyed, _bogie_spawned, _bogie_vel
    global _bogie_pos, _bogie_mode, _bogie_target_sep, _bogie_prev_pos
    global _bogie_last_frame, _bogie_repeat_count, _bogie_stall_count

    if _ax is None or _bog_x is None or _bog_y is None or _bog_z is None:
        return
    if _bogie_destroyed:
        if _bogie_glow is not None:
            try:
                _bogie_glow.remove()
            except Exception:
                pass
            _bogie_glow = None
        return
    spawned_now = False
    if not _bogie_hit and not _bogie_spawned:
        if _bogie_appear_at is None or frame < _bogie_appear_at:
            return
        plane_pos = RUNTIME.flight.plane_pos
        plane_vel = RUNTIME.flight.plane_vel
        px, py, pz = plane_pos
        vx, vy, _ = plane_vel
        speed_xy = math.hypot(vx, vy)
        if speed_xy < 1.0e-3:
            heading_x, heading_y = 1.0, 0.0
        else:
            heading_x, heading_y = vx / speed_xy, vy / speed_xy
        spawn_x, spawn_y, spawn_z = _compute_spawn_pos(px, py, pz, heading_x, heading_y)
        _bog_x[frame], _bog_y[frame], _bog_z[frame] = spawn_x, spawn_y, spawn_z
        _bogie_pos = (spawn_x, spawn_y, spawn_z)
        _bogie_spawned = True
        _bogie_mode = "approach"
        _bogie_prev_pos = (spawn_x, spawn_y, spawn_z)
        spawned_now = True

    # create mesh lazily -----------------------------------------------------
    if _bogie is None:
        _bogie = create_bogie_model((0, 0, 0), (0, 0, 0))
        _ax.add_collection3d(_bogie)             # type: ignore[arg-type]

    if _bogie_pos is None:
        bx = _bog_x[frame]
        by = _bog_y[frame]
        bz = _bog_z[frame]
        if (np.isnan(bx) or np.isnan(by) or np.isnan(bz)) and frame > 0:
            prev_x = _bog_x[frame - 1]
            prev_y = _bog_y[frame - 1]
            prev_z = _bog_z[frame - 1]
            if not (np.isnan(prev_x) or np.isnan(prev_y) or np.isnan(prev_z)):
                bx, by, bz = prev_x, prev_y, prev_z
        if not (np.isnan(bx) or np.isnan(by) or np.isnan(bz)):
            _bogie_pos = (float(bx), float(by), float(bz))
    if _bogie_pos is None:
        return


    bx, by, bz = _bogie_pos
    if not (math.isfinite(bx) and math.isfinite(by) and math.isfinite(bz)):
        bx, by, bz = _unstick_bogie(frame, float(bx), float(by), float(bz))
        _bogie_pos = (bx, by, bz)
    pre_pos = _bogie_pos
    if not _bogie_hit and _bogie_spawned:
        move_ok = True
        if _bogie_last_frame == frame:
            _bogie_repeat_count += 1
            move_ok = _bogie_repeat_count >= _BOGIE_REPEAT_MOVE_INTERVAL
            if move_ok:
                _bogie_repeat_count = 0
        else:
            _bogie_last_frame = frame
            _bogie_repeat_count = 0
        if not spawned_now and move_ok:
            reached = False
            if _bogie_mode == "approach":
                bx, by, bz, reached = _approach_step(frame, float(bx), float(by), float(bz))
                if reached:
                    _bogie_mode = "dogfight"
                    _bogie_vel = None
            else:
                bx, by, bz = _dogfight_step(frame, float(bx), float(by), float(bz))
            _bogie_pos = (bx, by, bz)
        if frame < _bog_x.size:
            _bog_x[frame], _bog_y[frame], _bog_z[frame] = bx, by, bz
        dx = _bogie_pos[0] - pre_pos[0]
        dy = _bogie_pos[1] - pre_pos[1]
        dz = _bogie_pos[2] - pre_pos[2]
        move_dist = math.sqrt(dx * dx + dy * dy + dz * dz)

    # post-hit tumble --------------------------------------------------------
    if _bogie_hit and not _bogie_destroyed:
        if _bogie_hit_origin is None:
            if np.isnan(bx) or np.isnan(by) or np.isnan(bz):
                return
            _bogie_hit_origin = (float(bx), float(by), float(bz))
        if _bogie_hit_tick is None:
            _bogie_hit_tick = 0
        t = _bogie_hit_tick
        ox, oy, oz = _bogie_hit_origin

        dt = max(_cfg.SIM_DT_MS / 1000.0, 1e-6)
        t_sec = float(t) * dt
        drift = 40.0 + (6.0 * t)
        bx = ox + drift * math.cos(0.30 * t)
        by = oy + drift * math.sin(0.30 * t)
        fall = (_BOGIE_FALL_SPEED * t_sec) + (0.5 * _BOGIE_FALL_GRAVITY * t_sec * t_sec)
        bz = oz - fall
        if frame < _bog_x.size:
            _bog_x[frame], _bog_y[frame], _bog_z[frame] = bx, by, bz
        _bogie_pos = (float(bx), float(by), float(bz))

        if not _parachute_deployed:
            spawn_parachute((bx, by, bz + 80.0))
            _parachute_deployed = True

        ground_z = float(sample_height(bx, by, default=_cfg.TERRAIN_ZMIN))
        if bz <= ground_z + 1.0 or t_sec >= _BOGIE_FALL_MAX_SECONDS:
            spawn_explosion((bx, by, ground_z))
            if _bogie:
                _bogie.remove()
            _bogie = None
            _bogie_destroyed = True
            _bog_x[frame + 1:], _bog_y[frame + 1:], _bog_z[frame + 1:] = np.nan, np.nan, np.nan
            return

        if _bogie:
            if _bogie_fall_prev is None:
                dv = (0.0, 0.0, 0.0)
            else:
                dv = (
                    bx - _bogie_fall_prev[0],
                    by - _bogie_fall_prev[1],
                    bz - _bogie_fall_prev[2],
                )
            update_mesh(_bogie, (bx, by, bz), dv, scale=BOGIE_SCALE)
            _update_glow(bx, by, bz)
        _bogie_fall_prev = (bx, by, bz)
        _bogie_hit_tick += 1
        return

    # normal flight update ---------------------------------------------------
    if not _bogie_destroyed and _bogie:
        ground_z = float(sample_height(bx, by, default=bz))
        min_z = ground_z + _BOGIE_TERRAIN_CLEARANCE
        if bz < min_z:
            bz = min_z
            if frame < _bog_z.size:
                _bog_z[frame] = bz
        _bogie_pos = (float(bx), float(by), float(bz))
        if _bogie_prev_pos is None:
            dv = (0.0, 0.0, 0.0)
        else:
            dv = (
                bx - _bogie_prev_pos[0],
                by - _bogie_prev_pos[1],
                bz - _bogie_prev_pos[2],
            )
            if not _bogie_hit and _bogie_spawned:
                move_dist = math.sqrt((dv[0] * dv[0]) + (dv[1] * dv[1]) + (dv[2] * dv[2]))
                if not math.isfinite(move_dist):
                    move_dist = 0.0
                if move_dist < _BOGIE_STALL_EPS:
                    _bogie_stall_count += 1
                else:
                    _bogie_stall_count = 0
                if _bogie_stall_count >= _BOGIE_STALL_RESET_FRAMES:
                    bx, by, bz = _unstick_bogie(frame, float(bx), float(by), float(bz))
                    _bogie_pos = (float(bx), float(by), float(bz))
                    _bogie_prev_pos = _bogie_pos
                    _bogie_vel = None
                    _bogie_mode = "dogfight"
                    _bogie_weave_phase = 0.0
                    _bogie_repeat_count = 0
                    _bogie_stall_count = 0
        update_mesh(_bogie, (bx, by, bz), dv, scale=BOGIE_SCALE)
        _update_glow(bx, by, bz)
        _bogie_prev_pos = (float(bx), float(by), float(bz))

    # deterministic single “hit” --------------------------------------------
    hit_frame = _hit_frame_override
    if hit_frame is not None:
        if frame == hit_frame and not _bogie_hit:
            _bogie_hit = True
            _bogie_hit_at = frame
            _bogie_hit_tick = 0
            _bogie_hit_origin = (float(bx), float(by), float(bz))
            _bogie_fall_prev = None
    elif not _bogie_hit:
        weapon = _check_projectile_hit(bx, by, bz)
        if weapon is not None:
            _bogie_hit = True
            _bogie_hit_at = frame
            _bogie_hit_tick = 0
            _bogie_hit_origin = (float(bx), float(by), float(bz))
            _bogie_fall_prev = None
            spawn_explosion((float(bx), float(by), float(bz)), scale=_BOGIE_HIT_EXPLOSION_SCALE)
            _record_impact(frame, bx, by, bz, target="bogie", weapon=weapon)



def _blast_scale(scale: float) -> float:
    if not math.isfinite(scale) or scale <= 0.0:
        return 1.0
    factor = float(scale) / _BOGIE_BLAST_SCALE_REF
    return max(0.5, min(2.0, factor))


def apply_bomb_blast(
    frame: int,
    centre: Tuple[float, float, float],
    *,
    scale: float = 1.0,
) -> None:
    """Apply bomb proximity damage to the bogie."""
    global _bogie_hit, _bogie_hit_at, _bogie_hit_tick, _bogie_hit_origin, _bogie_fall_prev
    global _bogie_hp, _bogie_damaged
    if _bogie_destroyed or _bogie_hit or not _bogie_spawned:
        return
    if _bogie_pos is None:
        return
    bx, by, bz = _bogie_pos
    scale_factor = _blast_scale(scale)
    kill_r = _BOGIE_BLAST_KILL_RADIUS * scale_factor
    dmg_r = _BOGIE_BLAST_DAMAGE_RADIUS * scale_factor
    if dmg_r <= 0.0:
        return
    dx = bx - centre[0]
    dy = by - centre[1]
    dz = bz - centre[2]
    dist = math.sqrt(dx * dx + dy * dy + dz * dz)
    if dist <= kill_r:
        _bogie_hp = 0.0
        _bogie_hit = True
        _bogie_hit_at = frame
        _bogie_hit_tick = 0
        _bogie_hit_origin = (float(bx), float(by), float(bz))
        _bogie_fall_prev = None
        spawn_explosion((float(bx), float(by), float(bz)), scale=_BOGIE_HIT_EXPLOSION_SCALE)
        _record_impact(frame, bx, by, bz, target="bogie", weapon="bomb")
        return
    if dist <= dmg_r:
        span = max(dmg_r - kill_r, 1.0)
        falloff = 1.0 - (dist - kill_r) / span
        damage = max(_BOGIE_BLAST_MIN_DAMAGE, falloff * _BOGIE_BLAST_DAMAGE_SCALE)
        _bogie_hp = max(0.0, _bogie_hp - damage)
        if _bogie_hp <= 0.0:
            _bogie_hit = True
            _bogie_hit_at = frame
            _bogie_hit_tick = 0
            _bogie_hit_origin = (float(bx), float(by), float(bz))
            _bogie_fall_prev = None
            spawn_explosion((float(bx), float(by), float(bz)), scale=_BOGIE_HIT_EXPLOSION_SCALE)
            _record_impact(frame, bx, by, bz, target="bogie", weapon="bomb")
        else:
            _bogie_damaged = True
