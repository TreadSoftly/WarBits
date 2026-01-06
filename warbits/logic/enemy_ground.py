from __future__ import annotations

# ─────────────────────────────────────────────────────────────────────────────
# logic/enemy_ground.py – AAA emplacements (runtime + simple AI tracking)
# ─────────────────────────────────────────────────────────────────────────────
import math
import os
import random
from dataclasses import dataclass
from typing import Any, Tuple, List, cast

import numpy as np
import numpy.typing as npt
from mpl_toolkits.mplot3d import Axes3D       # type: ignore
from mpl_toolkits.mplot3d.art3d import Poly3DCollection  # type: ignore

from ..config import settings as _cfg
from ..core.events import ImpactEvent
from ..physics.terrain import sample_height
from ..logic.state import RUNTIME
from ..physics.explosions import spawn_explosion

__all__ = [
    "init",
    "reset",
    "update",
    "check_hits",
    "apply_bomb_blast",
    "get_targets",
    "get_targets_with_ids",
    "get_home_targets_with_ids",
    "get_anchor",
    "configure",
    "has_live_targets",
]

# --------------------------------------------------------------------------- #
# Runtime handles
# --------------------------------------------------------------------------- #
_ax: Axes3D | None = None
_cols: List[Poly3DCollection] = []
_emplacements: List["_Emplacement"] = []
_ANGLE_EPS_DEG = 1.0
_EMPLACEMENT_HIT_RADIUS_BULLET = 220.0
_EMPLACEMENT_HIT_RADIUS_ROCKET = 320.0
_EMPLACEMENT_HIT_RADIUS_BOMB = 520.0
_EMPLACEMENT_HIT_RADIUS_BULLET_SQ = _EMPLACEMENT_HIT_RADIUS_BULLET ** 2
_EMPLACEMENT_HIT_RADIUS_ROCKET_SQ = _EMPLACEMENT_HIT_RADIUS_ROCKET ** 2
_EMPLACEMENT_HIT_RADIUS_BOMB_SQ = _EMPLACEMENT_HIT_RADIUS_BOMB ** 2
_BLAST_KILL_RADIUS_BOMB = 820.0
_BLAST_DAMAGE_RADIUS_BOMB = 1650.0
_BLAST_DAMAGE_SCALE = 0.65
_BLAST_MIN_DAMAGE = 0.12
_BLAST_SCALE_REF = 9.0
_PATROL_RADIUS = 1600.0
_PATROL_REACHED = 250.0
_PATROL_ORBIT_MIN = 450.0
_PATROL_ORBIT_MAX = 1300.0
_PATROL_TIMER_MIN = 120
_PATROL_TIMER_MAX = 260
_ENGAGE_RADIUS = 7500.0
_ENGAGE_EXIT_RADIUS = _ENGAGE_RADIUS * 1.15
_ENGAGE_ORBIT_RADIUS = 2000.0
_EVADE_RADIUS = 2200.0
_EVADE_EXIT_RADIUS = _EVADE_RADIUS * 1.20
_HOME_RADIUS = 3600.0
_PATROL_SPEED = 18.0
_ENGAGE_SPEED = 26.0
_EVADE_SPEED = 34.0
_TURN_RATE = 0.16
_SPAWN_JITTER = 450.0
_BOUNDS_MARGIN = 250.0
_rng = random.Random()
_GROUND_COUNT_DEFAULT = 6


def _read_ground_count() -> int:
    raw = os.environ.get("WARBITS_GROUND_COUNT", "").strip()
    if not raw:
        return _GROUND_COUNT_DEFAULT
    try:
        value = int(raw)
    except ValueError:
        return _GROUND_COUNT_DEFAULT
    return max(2, value)


_GROUND_COUNT = _read_ground_count()

# --------------------------------------------------------------------------- #
# Low-level geometry helpers
# --------------------------------------------------------------------------- #
_F32Arr = npt.NDArray[np.float32]


def _box_faces(size: float, z0: float, z1: float) -> _F32Arr:
    half = size / 2.0
    base = np.array(
        [
            (-half, -half, z0),
            (half, -half, z0),
            (half, half, z0),
            (-half, half, z0),
        ],
        dtype=np.float32,
    )
    top = base.copy()
    top[:, 2] = z1
    return np.array(
        [
            base,
            top,
            [base[0], base[1], top[1], top[0]],
            [base[1], base[2], top[2], top[1]],
            [base[2], base[3], top[3], top[2]],
            [base[3], base[0], top[0], top[3]],
        ],
        dtype=np.float32,
    )


def _rotate_faces_z(
    faces: _F32Arr,
    angle_rad: float,
    *,
    out: _F32Arr | None = None,
) -> _F32Arr:
    c = math.cos(angle_rad)
    s = math.sin(angle_rad)
    rotated = faces.copy() if out is None else out
    if out is not None:
        np.copyto(rotated, faces)
    x = rotated[..., 0]
    y = rotated[..., 1]
    rotated[..., 0] = x * c - y * s
    rotated[..., 1] = x * s + y * c
    return rotated


@dataclass
class _Emplacement:
    base_faces: _F32Arr
    turret_base: _F32Arr
    turret_faces: _F32Arr
    world_faces: _F32Arr
    last_angle_deg: float
    center: Tuple[float, float, float]
    home_xy: Tuple[float, float]
    patrol_xy: Tuple[float, float]
    orbit_dir: int
    orbit_radius: float
    patrol_timer: int
    vx: float
    vy: float
    mode: str
    last_frame: int
    destroyed: bool
    hp: float
    damaged: bool


def _scene_bounds() -> tuple[float, float, float, float]:
    x_min = float(_cfg.TERRAIN_XMIN)
    x_max = float(_cfg.TERRAIN_XMAX)
    y_min = float(_cfg.TERRAIN_YMIN)
    y_max = float(_cfg.TERRAIN_YMAX)
    span_x = max(1.0, x_max - x_min)
    span_y = max(1.0, y_max - y_min)
    margin = max(_BOUNDS_MARGIN, 0.05 * min(span_x, span_y))
    if span_x > 2.0 * margin:
        x_min += margin
        x_max -= margin
    if span_y > 2.0 * margin:
        y_min += margin
        y_max -= margin
    return x_min, x_max, y_min, y_max


def _clamp_xy(x: float, y: float) -> tuple[float, float]:
    xmin, xmax, ymin, ymax = _scene_bounds()
    return max(xmin, min(xmax, x)), max(ymin, min(ymax, y))


def _pick_patrol_target(home_x: float, home_y: float) -> tuple[float, float]:
    angle = _rng.uniform(0.0, 2.0 * math.pi)
    radius = _rng.uniform(0.35 * _PATROL_RADIUS, _PATROL_RADIUS)
    tx = home_x + math.cos(angle) * radius
    ty = home_y + math.sin(angle) * radius
    return _clamp_xy(tx, ty)


def _build_placements(count: int) -> list[tuple[float, float]]:
    if count <= 0:
        return []
    xmin, xmax, ymin, ymax = _scene_bounds()
    span_x = max(1.0, xmax - xmin)
    span_y = max(1.0, ymax - ymin)
    center_x = (xmin + xmax) / 2.0
    center_y = (ymin + ymax) / 2.0
    span = min(span_x, span_y)
    placements: list[tuple[float, float]] = []
    if count == 1:
        placements.append((center_x, center_y))
        return placements

    cluster_count = 2 if count <= 4 else 3
    cluster_radius = max(1500.0, 0.18 * span)
    cluster_centers: list[tuple[float, float]] = []
    for i in range(cluster_count):
        angle = (2.0 * math.pi * i / cluster_count) + _rng.uniform(-0.45, 0.45)
        radius = cluster_radius * _rng.uniform(0.85, 1.15)
        if i == 0 and cluster_count > 1:
            radius *= 1.35
        cx = center_x + math.cos(angle) * radius + _rng.uniform(-0.04 * span, 0.04 * span)
        cy = center_y + math.sin(angle) * radius + _rng.uniform(-0.04 * span, 0.04 * span)
        cluster_centers.append(_clamp_xy(cx, cy))

    base_n = count // cluster_count
    remainder = count % cluster_count
    cluster_spread = max(380.0, 0.05 * span)
    for i, (cx, cy) in enumerate(cluster_centers):
        n = base_n + (1 if i < remainder else 0)
        for _ in range(n):
            angle = _rng.uniform(0.0, 2.0 * math.pi)
            radius = cluster_spread * _rng.uniform(0.25, 0.85)
            x = cx + math.cos(angle) * radius + _rng.uniform(-0.02 * span, 0.02 * span)
            y = cy + math.sin(angle) * radius + _rng.uniform(-0.02 * span, 0.02 * span)
            x, y = _clamp_xy(x, y)
            placements.append((x, y))
    return placements


def _reset_patrol(emp: "_Emplacement") -> None:
    emp.patrol_xy = _pick_patrol_target(emp.home_xy[0], emp.home_xy[1])
    emp.orbit_dir = 1 if _rng.random() < 0.5 else -1
    emp.orbit_radius = _rng.uniform(_PATROL_ORBIT_MIN, _PATROL_ORBIT_MAX)
    emp.patrol_timer = _rng.randint(_PATROL_TIMER_MIN, _PATROL_TIMER_MAX)


def _orbit_vector(
    x: float,
    y: float,
    cx: float,
    cy: float,
    radius: float,
    orbit_dir: int,
    *,
    radial_gain: float = 0.6,
) -> tuple[float, float]:
    dx = x - cx
    dy = y - cy
    dist = math.hypot(dx, dy)
    if dist < 1e-6:
        return float(orbit_dir), 0.0
    tan_x = -dy / dist
    tan_y = dx / dist
    err = (dist - radius) / max(radius, 1.0)
    radial_x = dx / dist
    radial_y = dy / dist
    return (
        tan_x * orbit_dir - radial_x * err * radial_gain,
        tan_y * orbit_dir - radial_y * err * radial_gain,
    )


def configure(seed: int | None) -> None:
    """Seed the ground-movement RNG so loops are reproducible when desired."""
    global _rng
    _rng = random.Random(seed) if seed is not None else random.Random()


def _advance(
    frame: int,
    *,
    tgt_x: float | None,
    tgt_y: float | None,
) -> None:
    if not _emplacements:
        return
    if tgt_x is None or tgt_y is None:
        plane_x, plane_y, _ = RUNTIME.flight.plane_pos
        tgt_x = plane_x
        tgt_y = plane_y
    for emp in _emplacements:
        if emp.destroyed:
            continue
        if emp.last_frame == frame:
            continue
        x, y, _ = emp.center
        dx = tgt_x - x
        dy = tgt_y - y
        dist = math.hypot(dx, dy)

        mode = emp.mode if emp.mode else "patrol"
        if mode == "evade":
            if dist > _EVADE_EXIT_RADIUS:
                mode = "engage" if dist <= _ENGAGE_RADIUS else "patrol"
        elif mode == "engage":
            if dist > _ENGAGE_EXIT_RADIUS:
                mode = "patrol"
        else:
            if dist <= _EVADE_RADIUS:
                mode = "evade"
            elif dist <= _ENGAGE_RADIUS:
                mode = "engage"

        if mode != emp.mode:
            emp.mode = mode
            if mode == "patrol":
                _reset_patrol(emp)
            else:
                emp.orbit_dir = 1 if _rng.random() < 0.5 else -1

        if mode == "evade":
            speed = _EVADE_SPEED
            perp_x, perp_y = -dy, dx
            desired_x = -dx + perp_x * 0.35 * emp.orbit_dir
            desired_y = -dy + perp_y * 0.35 * emp.orbit_dir
        elif mode == "engage":
            speed = _ENGAGE_SPEED
            desired_x, desired_y = _orbit_vector(
                x,
                y,
                tgt_x,
                tgt_y,
                _ENGAGE_ORBIT_RADIUS,
                emp.orbit_dir,
                radial_gain=0.45,
            )
        else:
            speed = _PATROL_SPEED
            emp.patrol_timer -= 1
            patrol_dx = emp.patrol_xy[0] - x
            patrol_dy = emp.patrol_xy[1] - y
            patrol_dist = math.hypot(patrol_dx, patrol_dy)
            if patrol_dist <= _PATROL_REACHED or emp.patrol_timer <= 0:
                _reset_patrol(emp)
                patrol_dx = emp.patrol_xy[0] - x
                patrol_dy = emp.patrol_xy[1] - y
                patrol_dist = math.hypot(patrol_dx, patrol_dy)
            if patrol_dist > emp.orbit_radius * 1.6:
                desired_x = patrol_dx
                desired_y = patrol_dy
            else:
                desired_x, desired_y = _orbit_vector(
                    x,
                    y,
                    emp.patrol_xy[0],
                    emp.patrol_xy[1],
                    emp.orbit_radius,
                    emp.orbit_dir,
                )

        desired_len = math.hypot(desired_x, desired_y)
        if desired_len < 1e-6:
            desired_x = _rng.uniform(-1.0, 1.0)
            desired_y = _rng.uniform(-1.0, 1.0)
            desired_len = math.hypot(desired_x, desired_y)

        desired_x /= desired_len
        desired_y /= desired_len

        emp.vx = (1.0 - _TURN_RATE) * emp.vx + _TURN_RATE * desired_x * speed
        emp.vy = (1.0 - _TURN_RATE) * emp.vy + _TURN_RATE * desired_y * speed

        x += emp.vx
        y += emp.vy
        x, y = _clamp_xy(x, y)

        home_dx = x - emp.home_xy[0]
        home_dy = y - emp.home_xy[1]
        if math.hypot(home_dx, home_dy) > _HOME_RADIUS:
            back_len = math.hypot(home_dx, home_dy) or 1.0
            x -= (home_dx / back_len) * _TURN_RATE * speed
            y -= (home_dy / back_len) * _TURN_RATE * speed

        z = float(sample_height(x, y, default=0.0))
        emp.center = (x, y, z)
        emp.last_frame = frame


def _segment_any_hit(
    paths: _F32Arr,
    sample_index: npt.NDArray[np.int32],
    tx: float,
    ty: float,
    tz: float,
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
    w = np.array([tx, ty, tz], dtype=np.float32) - p0
    v_len_sq = np.sum(v * v, axis=1)
    dot = np.sum(w * v, axis=1)
    t = np.zeros_like(dot, dtype=np.float32)
    np.divide(dot, v_len_sq, out=t, where=v_len_sq > 1e-9)
    t = np.clip(t, 0.0, 1.0)
    closest = p0 + v * t[:, None]
    dx = closest[:, 0] - tx
    dy = closest[:, 1] - ty
    dz = closest[:, 2] - tz
    return bool(np.any(dx * dx + dy * dy + dz * dz <= radius_sq))


def _check_projectile_hit(tx: float, ty: float, tz: float) -> str | None:
    paths = RUNTIME.active_bullets.paths
    idx = RUNTIME.active_bullets.sample_index
    if _segment_any_hit(paths, idx, tx, ty, tz, _EMPLACEMENT_HIT_RADIUS_BULLET_SQ):
        return "bullet"
    paths = RUNTIME.active_rockets.paths
    idx = RUNTIME.active_rockets.sample_index
    if _segment_any_hit(paths, idx, tx, ty, tz, _EMPLACEMENT_HIT_RADIUS_ROCKET_SQ):
        return "rocket"
    paths = RUNTIME.active_bombs.paths
    idx = RUNTIME.active_bombs.sample_index
    if _segment_any_hit(paths, idx, tx, ty, tz, _EMPLACEMENT_HIT_RADIUS_BOMB_SQ):
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
    if os.environ.get("WARBITS_IMPACT_DEBUG", "").lower() in {"1", "true", "yes", "on"}:
        print(f"[impact] frame={frame} target={target} weapon={weapon} pos=({x:.1f},{y:.1f},{z:.1f})")


def _set_col_facecolor(col: Poly3DCollection, color: str) -> None:
    cast(Any, col).set_facecolor(color)

# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #
def init(ax: Axes3D) -> None:
    """Create (once) and register AAA Poly3DCollections on the given axes."""
    global _ax, _cols, _emplacements
    if _ax is not None and _ax is not ax and _cols:
        for col in _cols:
            try:
                col.remove()
            except Exception:
                pass
        _cols = []
        _emplacements = []
    _ax = ax
    if _cols:
        return  # already initialised

    base_variants = [
        (_box_faces(250.0, 0.0, 160.0), _box_faces(130.0, 160.0, 190.0)),
        (_box_faces(200.0, 0.0, 150.0), _box_faces(120.0, 150.0, 185.0)),
        (_box_faces(280.0, 0.0, 170.0), _box_faces(140.0, 170.0, 205.0)),
    ]
    _cols = []
    _emplacements = []
    for idx in range(_GROUND_COUNT):
        col = Poly3DCollection([], facecolor="red", edgecolor="black", alpha=1.0)
        col._aaa_flag = True        # type: ignore[attr-defined]  # debug helper
        ax.add_collection3d(col)    # type: ignore[arg-type]
        _cols.append(col)

        base_template, turret_template = base_variants[idx % len(base_variants)]
        base_faces = base_template.copy()
        turret_base = turret_template.copy()
        turret_faces = turret_template.copy()
        world_faces = np.empty(
            (base_faces.shape[0] + turret_faces.shape[0], *base_faces.shape[1:]),
            dtype=np.float32,
        )
        _emplacements.append(
            _Emplacement(
                base_faces=base_faces,
                turret_base=turret_base,
                turret_faces=turret_faces,
                world_faces=world_faces,
                last_angle_deg=1.0e9,
                center=(0.0, 0.0, 0.0),
                home_xy=(0.0, 0.0),
                patrol_xy=(0.0, 0.0),
                orbit_dir=1,
                orbit_radius=_PATROL_ORBIT_MIN,
                patrol_timer=0,
                vx=0.0,
                vy=0.0,
                mode="patrol",
                last_frame=-1,
                destroyed=False,
                hp=1.0,
                damaged=False,
            ),
        )


def reset() -> None:
    """Called once per animation loop restart (placeholder for future state)."""
    if not _emplacements or not _cols:
        return
    placements = _build_placements(len(_emplacements))
    if not placements:
        xmin, xmax, ymin, ymax = _scene_bounds()
        center = ((xmin + xmax) / 2.0, (ymin + ymax) / 2.0)
        placements = [center for _ in _emplacements]
    for idx, emp in enumerate(_emplacements):
        emp.destroyed = False
        emp.damaged = False
        emp.hp = 1.0
        emp.last_frame = -1
        if idx < len(placements):
            base_x, base_y = placements[idx]
        else:
            base_x, base_y = placements[-1]
        x = base_x + _rng.uniform(-_SPAWN_JITTER, _SPAWN_JITTER)
        y = base_y + _rng.uniform(-_SPAWN_JITTER, _SPAWN_JITTER)
        x, y = _clamp_xy(x, y)
        z = float(sample_height(x, y, default=0.0))
        emp.center = (x, y, z)
        emp.home_xy = (x, y)
        _reset_patrol(emp)
        emp.vx = 0.0
        emp.vy = 0.0
        emp.mode = "patrol"
    for col in _cols:
        try:
            col.set_visible(True)
            _set_col_facecolor(col, "red")
        except Exception:
            pass


def _blast_scale(scale: float) -> float:
    if not math.isfinite(scale) or scale <= 0.0:
        return 1.0
    factor = float(scale) / _BLAST_SCALE_REF
    return max(0.5, min(2.0, factor))


def apply_bomb_blast(
    frame: int,
    centre: tuple[float, float, float],
    *,
    scale: float = 1.0,
) -> None:
    """Apply bomb proximity damage to emplacements."""
    if not _emplacements:
        return
    scale_factor = _blast_scale(scale)
    kill_r = _BLAST_KILL_RADIUS_BOMB * scale_factor
    dmg_r = _BLAST_DAMAGE_RADIUS_BOMB * scale_factor
    if dmg_r <= 0.0:
        return
    cx, cy, cz = centre
    for idx, emp in enumerate(_emplacements):
        if emp.destroyed:
            continue
        ex, ey, ez = emp.center
        dx = ex - cx
        dy = ey - cy
        dz = ez - cz
        dist = math.sqrt(dx * dx + dy * dy + dz * dz)
        if dist <= kill_r:
            emp.destroyed = True
            emp.hp = 0.0
            _record_impact(frame, ex, ey, ez, target=f"aaa_{idx}", weapon="bomb")
            try:
                _cols[idx].set_visible(False)
            except Exception:
                pass
            continue
        if dist <= dmg_r:
            span = max(dmg_r - kill_r, 1.0)
            falloff = 1.0 - (dist - kill_r) / span
            damage = max(_BLAST_MIN_DAMAGE, falloff * _BLAST_DAMAGE_SCALE)
            emp.hp = max(0.0, emp.hp - damage)
            if emp.hp <= 0.0:
                emp.destroyed = True
                _record_impact(frame, ex, ey, ez, target=f"aaa_{idx}", weapon="bomb")
                try:
                    _cols[idx].set_visible(False)
                except Exception:
                    pass
            elif not emp.damaged:
                emp.damaged = True
                try:
                    _set_col_facecolor(_cols[idx], "firebrick")
                except Exception:
                    pass


def check_hits(frame: int, *, advance: bool = True) -> None:
    """Per-frame projectile hit checks (decoupled from visual update cadence)."""
    if _ax is None or not _cols or not _emplacements:
        return
    if advance:
        _advance(frame, tgt_x=None, tgt_y=None)
    for idx, emp in enumerate(_emplacements):
        if emp.destroyed:
            continue
        gx, gy, gz = emp.center
        weapon = _check_projectile_hit(gx, gy, gz)
        if weapon is None:
            continue
        emp.destroyed = True
        if weapon == "bomb":
            spawn_explosion((gx, gy, gz), scale=9.0, style="mushroom")
        else:
            spawn_explosion((gx, gy, gz))
        _record_impact(frame, gx, gy, gz, target=f"aaa_{idx}", weapon=weapon)
        try:
            _cols[idx].set_visible(False)
        except Exception:
            pass


def get_targets(frame: int) -> list[Tuple[float, float, float]]:
    """Return live emplacement centers for targeting/aim assistance."""
    if not _emplacements:
        return []
    _advance(frame, tgt_x=None, tgt_y=None)
    targets: list[Tuple[float, float, float]] = []
    for emp in _emplacements:
        if emp.destroyed:
            continue
        targets.append(emp.center)
    return targets


def get_targets_with_ids(frame: int) -> list[tuple[int, Tuple[float, float, float]]]:
    """Return live emplacements with their list index for targeting."""
    if not _emplacements:
        return []
    _advance(frame, tgt_x=None, tgt_y=None)
    targets: list[tuple[int, Tuple[float, float, float]]] = []
    for idx, emp in enumerate(_emplacements):
        if emp.destroyed:
            continue
        targets.append((idx, emp.center))
    return targets


def get_home_targets_with_ids() -> list[tuple[int, Tuple[float, float, float]]]:
    """Return emplacement home centers without advancing simulation."""
    if not _emplacements:
        return []
    targets: list[tuple[int, Tuple[float, float, float]]] = []
    for idx, emp in enumerate(_emplacements):
        hx, hy = emp.home_xy
        hz = float(sample_height(hx, hy, default=0.0))
        targets.append((idx, (hx, hy, hz)))
    return targets


def get_anchor() -> tuple[float, float] | None:
    """Return the average spawn anchor for flight-plan targeting."""
    if not _emplacements:
        return None
    primary = _emplacements[0]
    try:
        return primary.home_xy
    except Exception:
        pass
    xs = 0.0
    ys = 0.0
    count = 0
    for emp in _emplacements:
        hx, hy = emp.home_xy
        xs += hx
        ys += hy
        count += 1
    if count == 0:
        return None
    return xs / count, ys / count


def has_live_targets() -> bool:
    """Return True if any emplacement is still alive."""
    return any(not emp.destroyed for emp in _emplacements)


def update(frame: int, tgt_x: float, tgt_y: float) -> None:
    """
    Per-frame update.  `tgt_x, tgt_y` is the current aircraft XY position so the
    turrets can track and orient their barrels.
    """
    if _ax is None or not _cols or not _emplacements:
        return

    _advance(frame, tgt_x=tgt_x, tgt_y=tgt_y)
    for idx, emp in enumerate(_emplacements):
        if emp.destroyed:
            try:
                _cols[idx].set_visible(False)
            except Exception:
                pass
            continue
        gx, gy, gz = emp.center
        angle_deg = math.degrees(math.atan2(tgt_y - gy, tgt_x - gx))
        if abs(angle_deg - emp.last_angle_deg) >= _ANGLE_EPS_DEG:
            _rotate_faces_z(emp.turret_base, math.radians(angle_deg), out=emp.turret_faces)
            emp.last_angle_deg = angle_deg
        offset_vec = np.array([gx, gy, gz], dtype=np.float32)
        base_len = emp.base_faces.shape[0]
        emp.world_faces[:base_len] = emp.base_faces
        emp.world_faces[base_len:] = emp.turret_faces
        np.add(emp.world_faces, offset_vec, out=emp.world_faces)
        _cols[idx].set_verts(emp.world_faces)         # type: ignore[arg-type]
