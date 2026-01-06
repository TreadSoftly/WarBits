# ── warbits/scene/animation.py ────────────────────────────────────────────
# pyright: reportMissingTypeStubs=false, reportUnknownMemberType=false
from __future__ import annotations

import itertools
import math
import os
import random
import secrets
import time
from collections import deque
from typing import Any, Callable, Deque, Iterable, Tuple, cast

from matplotlib.animation import FuncAnimation
from matplotlib.artist import Artist
import numpy as np
from numpy.typing import NDArray

from ..config import settings as _cfg
from ..core.sim import Simulation
from ..logic import (
    enemy_ground as _ground,
    enemy_bogies as _bogies,
    RUNTIME,
    register_aircraft_axes as _register_ac_axes,
    reset_aircraft,
    step_aircraft,
)
from ..logic.aircraft import AIRCRAFT_SCALE
from ..logic.aircraft_hits import check_aircraft_hits as _check_aircraft_hits
from ..logic.scenario import ActionSchedule, ScenarioDirector, DecisionDirector, DecisionState
from ..logic.weather import WeatherDirector, WeatherState
from ..physics import (
    ballistics as _bullets,
    bombs_step, bombs_reset, bombs_schedule_release,            # bombs façade
)
from ..physics import rockets as _rockets                      # full rockets module
from ..logic.flight_paths import (
    DEFAULT_PHASES as _PHASES,
    build_flight_plan as _build_plan,
)
from ..physics.terrain import draw_terrain as _draw_terrain, sample_height as _sample_height
from ..physics.parachute import (
    register_axes as _register_para_axes,
    update_parachute,
    reset_parachute,
    active_count as _parachute_count,
)
from ..physics.explosions import register_axes, update_explosion, active_count as _explosion_count

# ───────────────────────── 1 · flight-plan ────────────────────────────────
PHASES = _PHASES
_flight_plan = _build_plan(PHASES)
flight_x: NDArray[np.float64]
flight_y: NDArray[np.float64]
flight_z: NDArray[np.float64]
flight_vx: NDArray[np.float64]
flight_vy: NDArray[np.float64]
flight_vz: NDArray[np.float64]
slice_map: dict[str, tuple[int, int]]
flight_x, flight_y, flight_z, slice_map = _flight_plan
n_frames: int = int(cast(Any, flight_x.size))
flight_vx = np.empty_like(flight_x)
flight_vy = np.empty_like(flight_y)
flight_vz = np.empty_like(flight_z)

# animation timing (ms)
FRAME_INTERVAL_MS = _cfg.FRAME_INTERVAL_MS
SIM_DT_MS = _cfg.SIM_DT_MS
SIM_REALTIME = _cfg.SIM_REALTIME
SIM_MAX_STEPS = _cfg.SIM_MAX_STEPS
_DT_S = max(SIM_DT_MS / 1000.0, 1e-6)

# bomb release timing is configured per loop

# scenario scheduling
_scenario_director = ScenarioDirector(seed=_cfg.SCENARIO_SEED)
_decision_director = DecisionDirector(seed=_cfg.SCENARIO_SEED)
_weather_director = WeatherDirector(seed=_cfg.SCENARIO_SEED)
_scenario: ActionSchedule | None = None
_decision_state: DecisionState = DecisionState(
    seed=0,
    phase_table=[],
    bullets_remaining=0,
    rockets_remaining=0,
    bombs_remaining=0,
)
_weather: WeatherState | None = None

# ───────────────────────── 2 · canvas / axes ──────────────────────────────
fig = None
ax = None
anim: FuncAnimation | None = None
_keep_ref: FuncAnimation | None = None
_hud_text = None
_simulation: Simulation | None = None
_last_update_start: float | None = None
_last_update_frame: int | None = None
_last_update_ms: float | None = None
_adaptive: _AdaptiveScaler | None = None
_adaptive_lod: _AdaptiveLOD | None = None
_sim_frame = 0
_combat_tick: int | None = None
_sim_started = False
_sim_accum_ms = 0.0
_sim_last_tick: float | None = None
_sim_done = False
_finish_after_render = False
_last_fullscreen_guard: float | None = None
_sim_pos_prev: tuple[float, float, float] | None = None
_sim_pos_curr: tuple[float, float, float] | None = None
_sim_vel_prev: tuple[float, float, float] | None = None
_sim_vel_curr: tuple[float, float, float] | None = None
_terrain_surface: Any | None = None
_terrain_base: tuple[int, int, int] | None = None
_terrain_profile: str | None = None
_terrain_seed: int | None = None
_terrain_lod: tuple[int, int, int, str | None, int | None] | None = None
_scene_bounds: tuple[float, float, float, float] | None = None
_scene_zlim: tuple[float, float] | None = None
_scene_center: tuple[float, float, float] | None = None
_scene_span: tuple[float, float, float] | None = None
_scene_limits: tuple[float, float, float, float, float, float] | None = None
_scene_dirty = False
_CAMERA_SMOOTH_ALPHA = 0.08
_CAMERA_DEADBAND_RATIO = 0.008
_CAMERA_DEADBAND_MIN = 20.0
_CAMERA_UPDATE_STRIDE = max(1, int(_cfg.CAMERA_UPDATE_STRIDE))
_camera_last_update = -1
_CAMERA_LIMIT_EPS_RATIO = 0.0025
_CAMERA_LIMIT_EPS_MIN = 12.0
_CAMERA_MODE = _cfg.CAMERA_MODE if _cfg.CAMERA_MODE in {"follow", "chase"} else "follow"
_CAMERA_LOOKAHEAD = _cfg.CAMERA_LOOKAHEAD
_CAMERA_HEIGHT = _cfg.CAMERA_HEIGHT
_CAMERA_ELEV = _cfg.CAMERA_ELEV
_CAMERA_AZIM_OFFSET = _cfg.CAMERA_AZIM_OFFSET
_CAMERA_HEADING_SMOOTH = _cfg.CAMERA_HEADING_SMOOTH
_CAMERA_LOCK_CENTER = _cfg.CAMERA_LOCK_CENTER
_camera_heading: float | None = None
_camera_view: tuple[float, float] | None = None
_EMPTY_TIMINGS: dict[str, float] = {}
_GROUND_UPDATE_STRIDE = 5
_AIRCRAFT_TERRAIN_CLEARANCE = _cfg.FLIGHT_TERRAIN_CLEARANCE
_BOMB_DROP_MAX_ALONG = 16000.0
_BOMB_DROP_MIN_ALONG = 350.0
_BOMB_DROP_MAX_LATERAL = 4500.0
_BOMB_DROP_UNDER_LATERAL = 650.0
_BOMB_DROP_MIN_ALT = 150.0
_BOMB_DROP_MIN_SPEED = 60.0
_BOMB_DROP_EARLY_FRAMES = 4
_BOMB_MIN_FRAME = 30
_WEAPON_MUZZLE_OFFSET = AIRCRAFT_SCALE * 1.6
_ADAPT_WARMUP_SECONDS = 2.0
_ADAPT_WARMUP_FRAMES = max(
    10,
    int((_ADAPT_WARMUP_SECONDS * 1000.0) / max(FRAME_INTERVAL_MS, 1)),
)
_adapt_warmup_remaining = _ADAPT_WARMUP_FRAMES
_startup_seed: int | None = None
_loop_counter = 0
_first_loop = True
_celebration_active = False
_celebration_hold_left = 0
_celebration_tick: int | None = None
_ground_tick: int | None = None
_loop_mode: str | None = None
_hold_dogfight_bounds: tuple[int, int, int, int] | None = None
_hold_ground_bounds: tuple[int, int, int, int] | None = None
_loop_start_pos: tuple[float, float, float] | None = None
_loop_reset_pending = True
_CELEBRATION_HOLD_SECONDS = _cfg.CELEBRATION_SECONDS
_CELEBRATION_HOLD_FRAMES = max(
    0,
    int(round((_CELEBRATION_HOLD_SECONDS * 1000.0) / max(SIM_DT_MS, 1e-6))),
)
_FIRE_CONE_DOT = math.cos(math.radians(75.0))
_GROUND_FIRE_CONE_DOT = math.cos(math.radians(82.0))
_GROUND_SEARCH_CONE_DOT = 0.0
_BULLET_FIRE_RANGE = 12000.0
_ROCKET_FIRE_RANGE = 14000.0
_PRIMARY_GROUND_ID = 0
_SECONDARY_GROUND_ID = 1
_GROUND_TACTICS = ("rocket", "strafe", "mixed")
_GROUND_FOCUS_SWITCH_RATIO = 0.75
_BOGIE_PRIORITY_RANGE = 12000.0
_GROUND_SEARCH_DIST = 13000.0
_ground_tactic: str | None = None
_ground_focus_id: int | None = None
_ground_focus_lock_until = 0
_GROUND_FOCUS_LOCK_FRAMES = 90
_last_bullet_fire = -10_000
_last_rocket_fire = -10_000
_FORCE_BULLET_GAP = 6
_FORCE_ROCKET_GAP = 12
_FORCED_BULLET_SPACING = 2
_FORCED_BULLET_BURST = 3
_primary_bomb_released = False
_MAX_ACTIVE_BULLETS = 240
_MAX_ACTIVE_ROCKETS = 16
_MAX_ACTIVE_BOMBS = 4
_bogie_expected = False
_bogie_seen = False
_ground_search_mode = False
_search_offset = (0.0, 0.0)
_SEARCH_OFFSET_GAIN = 0.03
_SEARCH_OFFSET_DECAY = 0.08
_SEARCH_OFFSET_MAX_RATIO = 0.20

# ───────────────────────── 3 · helpers ────────────────────────────────────
def _coerce_float(value: object, default: float = 0.0) -> float:
    if isinstance(value, bool):
        return default
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(cast(Any, value))
    except (TypeError, ValueError):
        return default


def _safe_len(value: object) -> int:
    try:
        return len(cast(Any, value))
    except Exception:
        return 0


def _lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def _lerp3(
    a: tuple[float, float, float],
    b: tuple[float, float, float],
    t: float,
) -> tuple[float, float, float]:
    return (_lerp(a[0], b[0], t), _lerp(a[1], b[1], t), _lerp(a[2], b[2], t))


def _wrap_angle_deg(angle: float) -> float:
    return (angle + 180.0) % 360.0 - 180.0


def _rand_range(rng: random.Random, bounds: tuple[int, int]) -> int:
    low, high = bounds
    if low >= high:
        return int(low)
    return rng.randint(int(low), int(high))


def _target_ahead(
    pos: tuple[float, float, float],
    vel: tuple[float, float, float],
    target: tuple[float, float, float],
    *,
    max_range: float,
    min_dot: float,
) -> bool:
    vx, vy, _ = vel
    speed_xy = math.hypot(vx, vy)
    if speed_xy < 1e-3:
        return False
    px, py, _ = pos
    tx, ty, _ = target
    dx = tx - px
    dy = ty - py
    dist_xy = math.hypot(dx, dy)
    if dist_xy < 1e-6 or dist_xy > max_range:
        return False
    dot = (dx * vx + dy * vy) / (dist_xy * speed_xy)
    return dot >= min_dot


def _target_under(
    pos: tuple[float, float, float],
    target: tuple[float, float, float],
    *,
    max_lateral: float,
    min_alt: float,
) -> bool:
    dx = target[0] - pos[0]
    dy = target[1] - pos[1]
    dist_xy = math.hypot(dx, dy)
    if dist_xy > max_lateral:
        return False
    return (pos[2] - target[2]) >= min_alt


def _first_target_ahead(
    targets: list[tuple[str, tuple[float, float, float]]],
    pos: tuple[float, float, float],
    vel: tuple[float, float, float],
    *,
    max_range: float,
    min_dot: float,
) -> tuple[str, tuple[float, float, float]] | None:
    for kind, target in targets:
        if _target_ahead(pos, vel, target, max_range=max_range, min_dot=min_dot):
            return kind, target
    return None


def _ground_targets_with_ids(frame: int) -> list[tuple[int, tuple[float, float, float]]]:
    getter = getattr(_ground, "get_targets_with_ids", None)
    if callable(getter):
        typed_getter = cast(
            Callable[[int], Iterable[tuple[int, tuple[float, float, float]]]],
            getter,
        )
        return list(typed_getter(frame))
    targets = cast(Iterable[tuple[float, float, float]], _ground.get_targets(frame))
    return [(idx, pos) for idx, pos in enumerate(targets)]


def _pick_ground_tactic(rng: random.Random) -> str:
    return rng.choice(_GROUND_TACTICS)


def _camera_center(
    pos: tuple[float, float, float],
    vel: tuple[float, float, float],
) -> tuple[float, float, float]:
    if _CAMERA_MODE != "chase":
        return pos
    vx, vy, _ = vel
    speed_xy = math.hypot(vx, vy)
    if speed_xy <= 1.0e-3 or _CAMERA_LOOKAHEAD <= 0.0:
        return pos[0], pos[1], pos[2] + _CAMERA_HEIGHT
    dir_x = vx / speed_xy
    dir_y = vy / speed_xy
    return (
        pos[0] + dir_x * _CAMERA_LOOKAHEAD,
        pos[1] + dir_y * _CAMERA_LOOKAHEAD,
        pos[2] + _CAMERA_HEIGHT,
    )


def _update_camera_view(vel: tuple[float, float, float]) -> None:
    global _camera_heading, _camera_view
    if ax is None or _CAMERA_MODE != "chase":
        return
    vx, vy, _ = vel
    speed_xy = math.hypot(vx, vy)
    if speed_xy <= 1.0e-3 and _camera_heading is None:
        return
    heading = (
        _camera_heading
        if speed_xy <= 1.0e-3 and _camera_heading is not None
        else math.degrees(math.atan2(vy, vx))
    )
    if _camera_heading is None:
        _camera_heading = heading
    else:
        delta = _wrap_angle_deg(heading - _camera_heading)
        _camera_heading += delta * _CAMERA_HEADING_SMOOTH
    azim = _camera_heading + _CAMERA_AZIM_OFFSET
    elev = _CAMERA_ELEV
    if _camera_view is not None:
        if abs(azim - _camera_view[0]) < 0.1 and abs(elev - _camera_view[1]) < 0.1:
            return
    ax.view_init(elev=elev, azim=azim)
    _camera_view = (azim, elev)


def _clamp_grid(step: int, rcount: int, ccount: int) -> tuple[int, int, int]:
    step = max(2, int(step))
    rcount = max(2, int(rcount))
    ccount = max(2, int(ccount))
    rcount = min(rcount, step)
    ccount = min(ccount, step)
    render_step = max(rcount, ccount)
    if step > render_step:
        step = render_step
    return step, rcount, ccount


def _compute_flight_velocities() -> None:
    global flight_vx, flight_vy, flight_vz
    if flight_x.size == 0:
        flight_vx = np.empty_like(flight_x)
        flight_vy = np.empty_like(flight_y)
        flight_vz = np.empty_like(flight_z)
        return
    flight_vx = np.empty_like(flight_x)
    flight_vy = np.empty_like(flight_y)
    flight_vz = np.empty_like(flight_z)
    if flight_x.size == 1:
        flight_vx[0] = 0.0
        flight_vy[0] = 0.0
        flight_vz[0] = 0.0
        return
    flight_vx[0] = 0.0
    flight_vy[0] = 0.0
    flight_vz[0] = 0.0
    flight_vx[1:] = np.diff(flight_x) / _DT_S
    flight_vy[1:] = np.diff(flight_y) / _DT_S
    flight_vz[1:] = np.diff(flight_z) / _DT_S


def _apply_flight_clearance() -> None:
    global flight_z
    if flight_x.size == 0 or flight_y.size == 0 or flight_z.size == 0:
        return
    ground = _sample_height(flight_x, flight_y, default=_cfg.TERRAIN_ZMIN)
    try:
        min_z = np.asarray(ground, dtype=np.float64) + _AIRCRAFT_TERRAIN_CLEARANCE
        if min_z.shape != flight_z.shape:
            min_z = np.broadcast_to(min_z, flight_z.shape)
        flight_z = np.maximum(flight_z, min_z)
    except Exception:
        return


def _aim_velocity(
    plane_pos: tuple[float, float, float],
    plane_vel: tuple[float, float, float],
    target_pos: tuple[float, float, float],
) -> tuple[float, float, float]:
    dx = target_pos[0] - plane_pos[0]
    dy = target_pos[1] - plane_pos[1]
    dz = target_pos[2] - plane_pos[2]
    dist = math.sqrt(dx * dx + dy * dy + dz * dz)
    if dist < 1e-6:
        return plane_vel
    speed = math.sqrt(
        plane_vel[0] * plane_vel[0]
        + plane_vel[1] * plane_vel[1]
        + plane_vel[2] * plane_vel[2]
    )
    if speed < 1e-3:
        speed = 1.0
    scale = speed / dist
    return (dx * scale, dy * scale, dz * scale)


def _weapon_origin(
    pos: tuple[float, float, float],
    vel: tuple[float, float, float],
) -> tuple[float, float, float]:
    vx, vy, vz = vel
    speed = math.sqrt(vx * vx + vy * vy + vz * vz)
    if speed <= 1.0e-3:
        return pos
    dir_x = vx / speed
    dir_y = vy / speed
    dir_z = vz / speed
    offset = _WEAPON_MUZZLE_OFFSET
    return (pos[0] + dir_x * offset, pos[1] + dir_y * offset, pos[2] + dir_z * offset)


def _ground_attack_bounds() -> tuple[int, int, int, int] | None:
    strafe = slice_map.get("Strafe")
    bombing = slice_map.get("Bombing")
    if strafe is None and bombing is None:
        return None
    if strafe is None:
        if bombing is None:
            return None
        start, end = bombing
    elif bombing is None:
        start, end = strafe
    else:
        start = min(int(strafe[0]), int(bombing[0]))
        end = max(int(strafe[1]), int(bombing[1]))
    start = int(start)
    end = int(end)
    length = end - start
    if length <= 1:
        return None
    span = length - 1
    period = span * 2
    if period <= 0:
        return None
    return start, end, span, period


def _ground_search_bounds() -> tuple[int, int, int, int] | None:
    strafe = slice_map.get("Strafe")
    bombing = slice_map.get("Bombing")
    escape = slice_map.get("Escape")
    segments = [seg for seg in (strafe, bombing, escape) if seg is not None]
    if not segments:
        approach = slice_map.get("Approach")
        segments = [seg for seg in (approach,) if seg is not None]
    if not segments:
        return _ground_attack_bounds()
    start = min(int(seg[0]) for seg in segments)
    end = max(int(seg[1]) for seg in segments)
    length = end - start
    if length <= 1:
        return None
    span = length - 1
    period = span * 2
    if period <= 0:
        return None
    return start, end, span, period


def _dogfight_bounds() -> tuple[int, int, int, int] | None:
    dogfight = slice_map.get("Dogfight")
    if dogfight is None:
        return None
    start, end = dogfight
    start = int(start)
    end = int(end)
    length = end - start
    if length <= 1:
        return None
    span = length - 1
    period = span * 2
    if period <= 0:
        return None
    return start, end, span, period


def _victory_bounds() -> tuple[int, int] | None:
    victory1 = slice_map.get("Victory1")
    victory2 = slice_map.get("Victory2")
    if victory1 is None and victory2 is None:
        return None
    if victory1 is not None:
        start, end = victory1
    elif victory2 is not None:
        start, end = victory2
    else:
        return None
    if victory2 is not None:
        end = victory2[1]
    start = int(start)
    end = int(end)
    if end <= start:
        return None
    return start, end


def _pingpong_loop_frame(tick: int, start: int, end: int) -> tuple[int, bool]:
    span = max(1, end - start)
    if span <= 1:
        return start, False
    period = (span - 1) * 2
    offset = tick % period
    if offset < span:
        return start + offset, (tick != 0 and offset == 0)
    back = offset - span
    return (end - 2) - back, False


def _reset_interpolation() -> None:
    global _sim_pos_prev, _sim_pos_curr, _sim_vel_prev, _sim_vel_curr
    _sim_pos_prev = None
    _sim_pos_curr = None
    _sim_vel_prev = None
    _sim_vel_curr = None


def _reset_loop_flags() -> None:
    global _combat_tick, _ground_tick, _loop_mode
    global _celebration_active, _celebration_hold_left, _celebration_tick
    global _bogie_expected, _bogie_seen
    global _hold_dogfight_bounds, _hold_ground_bounds
    _combat_tick = None
    _ground_tick = None
    _loop_mode = None
    _hold_dogfight_bounds = None
    _hold_ground_bounds = None
    _celebration_active = False
    _celebration_hold_left = 0
    _celebration_tick = None
    _bogie_expected = False
    _bogie_seen = False
    _reset_interpolation()


def _should_drop_bomb(
    pos: tuple[float, float, float],
    vel: tuple[float, float, float],
    target_pos: tuple[float, float, float] | None,
) -> bool:
    if target_pos is None:
        return False
    vx, vy, vz = vel
    speed_xy = math.hypot(vx, vy)
    if speed_xy < _BOMB_DROP_MIN_SPEED:
        return False
    px, py, pz = pos
    tx, ty, tz = target_pos
    dz = pz - tz
    if dz < _BOMB_DROP_MIN_ALT:
        return False
    # Predict impact point (no drag) so drops are aligned with target.
    g = 9.81
    disc = (vz * vz) + (2.0 * g * dz)
    if disc <= 0.0:
        return False
    t = (vz + math.sqrt(disc)) / g
    if t <= 0.0:
        return False
    along = speed_xy * t
    if along < _BOMB_DROP_MIN_ALONG or along > _BOMB_DROP_MAX_ALONG:
        return False
    impact_x = px + (vx * t)
    impact_y = py + (vy * t)
    lateral = math.hypot(impact_x - tx, impact_y - ty)
    if lateral > _BOMB_DROP_MAX_LATERAL:
        return False
    return True


def _set_terrain_context(loop_seed: int) -> None:
    global _terrain_profile, _terrain_seed
    _terrain_profile = _cfg.TERRAIN_PROFILE
    _terrain_seed = (int(loop_seed) + 1) & 0xFFFFFFFF


def _set_scene_bounds(center_x: float, center_y: float, center_z: float | None = None) -> None:
    global _scene_bounds, _scene_zlim, _scene_center, _scene_dirty
    if flight_x.size == 0 or flight_y.size == 0:
        if _scene_bounds is not None or _scene_zlim is not None:
            _scene_bounds = None
            _scene_zlim = None
            _scene_center = None
            _scene_dirty = True
        return
    size = max(1.0, float(_cfg.SCENE_SIZE))
    center_z_value = float(center_z) if center_z is not None else None
    prev_center = _scene_center
    if prev_center is None or (_CAMERA_LOCK_CENTER and _CAMERA_MODE == "follow"):
        smooth_x = center_x
        smooth_y = center_y
        if center_z_value is not None:
            smooth_z = center_z_value
        elif prev_center is not None:
            smooth_z = prev_center[2]
        else:
            smooth_z = 0.0
    else:
        alpha = _CAMERA_SMOOTH_ALPHA
        smooth_x = _lerp(prev_center[0], center_x, alpha)
        smooth_y = _lerp(prev_center[1], center_y, alpha)
        if center_z_value is not None:
            smooth_z = _lerp(prev_center[2], center_z_value, alpha)
        else:
            smooth_z = prev_center[2]
        deadband = max(_CAMERA_DEADBAND_MIN, size * _CAMERA_DEADBAND_RATIO)
        if (
            _scene_bounds is not None
            and abs(smooth_x - prev_center[0]) < deadband
            and abs(smooth_y - prev_center[1]) < deadband
            and abs(smooth_z - prev_center[2]) < deadband
        ):
            return
    half = size / 2.0
    _scene_bounds = (smooth_x - half, smooth_x + half, smooth_y - half, smooth_y + half)
    if _CAMERA_LOCK_CENTER and _CAMERA_MODE == "follow":
        z_span = max(3000.0, size * 0.8)
        half_z = z_span / 2.0
        z_min = smooth_z - half_z
        z_max = smooth_z + half_z
        if z_min < _cfg.TERRAIN_ZMIN:
            z_min = _cfg.TERRAIN_ZMIN
            z_max = z_min + z_span
        if z_max > _cfg.TERRAIN_ZMAX:
            z_max = _cfg.TERRAIN_ZMAX
            z_min = z_max - z_span
        _scene_zlim = (z_min, z_max)
    elif _scene_zlim is None:
        z_span = max(3000.0, size * 0.8)
        half_z = z_span / 2.0
        z_min = smooth_z - half_z
        z_max = smooth_z + half_z
        if z_min < _cfg.TERRAIN_ZMIN:
            z_min = _cfg.TERRAIN_ZMIN
            z_max = z_min + z_span
        if z_max > _cfg.TERRAIN_ZMAX:
            z_max = _cfg.TERRAIN_ZMAX
            z_min = z_max - z_span
        _scene_zlim = (z_min, z_max)
    _scene_center = (smooth_x, smooth_y, smooth_z)
    _scene_dirty = True


def _apply_scene_limits() -> None:
    global _scene_dirty, _scene_span, _scene_limits
    if ax is None or not _scene_dirty:
        return
    try:
        if _scene_bounds is None:
            x_min, x_max = _cfg.SCENE_XMIN, _cfg.SCENE_XMAX
            y_min, y_max = _cfg.SCENE_YMIN, _cfg.SCENE_YMAX
        else:
            x_min, x_max, y_min, y_max = _scene_bounds
        if _scene_zlim is None:
            z_min, z_max = _cfg.TERRAIN_ZMIN, _cfg.TERRAIN_ZMAX
        else:
            z_min, z_max = _scene_zlim
        span_x = abs(x_max - x_min)
        span_y = abs(y_max - y_min)
        span_z = abs(z_max - z_min)
        eps = max(_CAMERA_LIMIT_EPS_MIN, max(span_x, span_y) * _CAMERA_LIMIT_EPS_RATIO)
        if _scene_limits is not None:
            prev = _scene_limits
            if (
                abs(x_min - prev[0]) < eps
                and abs(x_max - prev[1]) < eps
                and abs(y_min - prev[2]) < eps
                and abs(y_max - prev[3]) < eps
                and abs(z_min - prev[4]) < eps
                and abs(z_max - prev[5]) < eps
            ):
                _scene_dirty = False
                return
        ax.set_xlim(x_min, x_max)
        ax.set_ylim(y_min, y_max)
        ax.set_zlim(z_min, z_max)
        if hasattr(ax, "set_box_aspect"):
            if _scene_span != (span_x, span_y, span_z):
                ax.set_box_aspect((max(span_x, 1.0), max(span_y, 1.0), max(span_z, 1.0)))
                _scene_span = (span_x, span_y, span_z)
        _scene_limits = (x_min, x_max, y_min, y_max, z_min, z_max)
        _scene_dirty = False
    except Exception:
        pass


def _should_update_camera(frame: int) -> bool:
    global _camera_last_update
    if frame <= 0 or _camera_last_update < 0:
        _camera_last_update = frame
        return True
    if (frame - _camera_last_update) < _CAMERA_UPDATE_STRIDE:
        return False
    _camera_last_update = frame
    return True


def _rebuild_terrain(step: int, rcount: int, ccount: int) -> None:
    global _terrain_surface, _terrain_lod, _terrain_profile, _terrain_seed
    if ax is None:
        return
    step, rcount, ccount = _clamp_grid(step, rcount, ccount)
    signature = (step, rcount, ccount, _terrain_profile, _terrain_seed)
    if _terrain_lod == signature:
        return
    if _terrain_surface is not None:
        try:
            _terrain_surface.remove()
        except Exception:
            pass
    try:
        _, _, _, _terrain_surface = _draw_terrain(
            ax,
            step=step,
            rcount=rcount,
            ccount=ccount,
            profile=_terrain_profile,
            seed=_terrain_seed,
            return_surface=True,
        )
    except Exception:
        _terrain_surface = None
    _apply_scene_limits()
    _terrain_lod = signature


def _reset_state() -> None:
    """Clear per-loop state *then* enqueue the next salvo of rockets."""
    bombs_reset()
    _rockets.reset()          # wipes in-flight rockets + launch queue
    _bullets.reset()
    _bogies.reset()
    reset_parachute()
    reset_aircraft()
    RUNTIME.impacts.clear()

    global _sim_pos_prev, _sim_pos_curr, _sim_vel_prev, _sim_vel_curr
    _sim_pos_prev = None
    _sim_pos_curr = None
    _sim_vel_prev = None
    _sim_vel_curr = None
    global _combat_tick
    _combat_tick = None
    global _ground_tick, _loop_mode
    _ground_tick = None
    _loop_mode = None
    global _scene_bounds, _scene_center, _scene_limits, _scene_span, _scene_zlim, _scene_dirty
    _scene_bounds = None
    _scene_center = None
    _scene_limits = None
    _scene_span = None
    _scene_zlim = None
    _scene_dirty = True
    global _camera_last_update, _camera_heading, _camera_view
    _camera_last_update = -1
    _camera_heading = None
    _camera_view = None
    global _celebration_active, _celebration_hold_left, _celebration_tick
    _celebration_active = False
    _celebration_hold_left = 0
    _celebration_tick = None

    global flight_x, flight_y, flight_z, slice_map, n_frames
    global _startup_seed, _adapt_warmup_remaining, _first_loop, _loop_start_pos, _loop_counter
    if _startup_seed is not None:
        loop_seed = _startup_seed
        _startup_seed = None
        _loop_counter = 0
    elif _cfg.SCENARIO_SEED is not None:
        _loop_counter += 1
        loop_seed = (_cfg.SCENARIO_SEED + _loop_counter) & 0xFFFFFFFF
    else:
        loop_seed = secrets.randbits(32)
    rng = random.Random(loop_seed)
    global _ground_tactic, _last_bullet_fire, _last_rocket_fire, _primary_bomb_released
    global _ground_focus_id, _ground_search_mode, _search_offset, _ground_focus_lock_until
    global _bogie_expected, _bogie_seen
    _ground_tactic = _pick_ground_tactic(rng)
    _last_bullet_fire = -10_000
    _last_rocket_fire = -10_000
    _primary_bomb_released = False
    _ground_focus_id = None
    _ground_focus_lock_until = 0
    _ground_search_mode = False
    _search_offset = (0.0, 0.0)
    _bogie_expected = False
    _bogie_seen = False
    _ground.configure(loop_seed)
    _ground.reset()
    target_xy = _ground.get_anchor()
    secondary_xy = None
    home_getter = getattr(_ground, "get_home_targets_with_ids", None)
    if callable(home_getter):
        typed_home_getter = cast(
            Callable[[], Iterable[tuple[int, tuple[float, float, float]]]],
            home_getter,
        )
        home_targets = list(typed_home_getter())
        home_targets.sort(key=lambda item: item[0])
        if home_targets:
            sum_x = sum(pos[0] for _, pos in home_targets)
            sum_y = sum(pos[1] for _, pos in home_targets)
            target_xy = (sum_x / len(home_targets), sum_y / len(home_targets))
        if len(home_targets) > 1 and target_xy is not None:
            farthest = max(
                home_targets,
                key=lambda item: (item[1][0] - target_xy[0]) ** 2 + (item[1][1] - target_xy[1]) ** 2,
            )
            secondary_pos = farthest[1]
            secondary_xy = (secondary_pos[0], secondary_pos[1])
    flight_x, flight_y, flight_z, slice_map = _build_plan(
        PHASES,
        rng=rng,
        target_xy=target_xy,
        secondary_xy=secondary_xy,
        start_pos=_loop_start_pos,
    )
    n_frames = int(cast(Any, flight_x.size))
    if flight_x.size:
        _loop_start_pos = (
            float(flight_x[0]),
            float(flight_y[0]),
            float(flight_z[0]),
        )
    if _first_loop:
        _adapt_warmup_remaining = max(_ADAPT_WARMUP_FRAMES, max(1, n_frames))
        _first_loop = False
    else:
        _adapt_warmup_remaining = _ADAPT_WARMUP_FRAMES

    _set_terrain_context(loop_seed)
    if _terrain_base is not None:
        _rebuild_terrain(*_terrain_base)
    _apply_flight_clearance()
    _compute_flight_velocities()
    if flight_x.size:
        _set_scene_bounds(float(flight_x[0]), float(flight_y[0]), float(flight_z[0]))
        _apply_scene_limits()

    _bogies.set_flight_path(flight_x, flight_y, flight_z, slice_map)

    global _scenario, _decision_state, _weather
    _scenario = _scenario_director.build(slice_map, seed=loop_seed)
    _decision_state = _decision_director.reset(slice_map, seed=_scenario.seed)
    _weather = _weather_director.build(seed=loop_seed)
    RUNTIME.environment.wind = _weather.wind
    RUNTIME.environment.gust = _weather.gust
    RUNTIME.environment.turbulence = _weather.turbulence
    RUNTIME.environment.visibility_km = _weather.visibility_km

    bogie_appear_at = _scenario.bogie_appear_frame
    dogfight_bounds = _dogfight_bounds()
    dogfight_start = int(dogfight_bounds[0]) if dogfight_bounds is not None else None
    ground_bounds = _ground_attack_bounds()
    if bogie_appear_at is None:
        if dogfight_start is not None:
            bogie_appear_at = dogfight_start
        elif ground_bounds is not None:
            start, end, _span, _period = ground_bounds
            if end > start:
                early_start = start + max(0, (end - start) // 6)
                bogie_appear_at = _rand_range(rng, (early_start, end - 1))
            else:
                bogie_appear_at = int(start)
        else:
            bogie_appear_at = int(max(0, min(n_frames - 1, n_frames // 3)))
    if dogfight_start is not None and bogie_appear_at > dogfight_start:
        bogie_appear_at = dogfight_start
    if ground_bounds is not None:
        start, end, _span, _period = ground_bounds
        if end > start:
            early_end = start + max(1, (end - start) // 2)
            early_end = min(end - 1, early_end)
            if bogie_appear_at < start or bogie_appear_at >= end:
                bogie_appear_at = _rand_range(rng, (start, early_end))
            else:
                bogie_appear_at = min(max(bogie_appear_at, start), early_end)
    bogie_appear_at = int(max(0, min(bogie_appear_at, n_frames - 1)))
    _bogies.configure(
        appear_at=bogie_appear_at,
        closing_factor=_scenario.bogie_closing_factor,
        hit_frame=_scenario.bogie_hit_frame if _cfg.BOGIE_SCRIPTED_HIT else None,
    )
    _bogie_expected = n_frames > 0


def _step_sim(frame: int) -> dict[str, float]:
    global _sim_frame, _sim_pos_prev, _sim_pos_curr, _sim_vel_prev, _sim_vel_curr
    global _loop_reset_pending
    global _last_bullet_fire, _last_rocket_fire, _primary_bomb_released, _bogie_seen
    global _ground_focus_id, _ground_search_mode, _search_offset, _ground_focus_lock_until
    if ax is None:
        return {}
    profile_enabled = False
    timings = {} if profile_enabled else _EMPTY_TIMINGS
    if frame == 0 and _loop_reset_pending:
        _loop_reset_pending = False
        _reset_state()

    prev_pos = _sim_pos_curr
    base_pos = (
        _coerce_float(flight_x[frame]),
        _coerce_float(flight_y[frame]),
        _coerce_float(flight_z[frame]),
    )
    pos = base_pos
    if prev_pos is None:
        vel = (
            _coerce_float(flight_vx[frame]),
            _coerce_float(flight_vy[frame]),
            _coerce_float(flight_vz[frame]),
        )
    else:
        vel = (
            (pos[0] - prev_pos[0]) / _DT_S,
            (pos[1] - prev_pos[1]) / _DT_S,
            (pos[2] - prev_pos[2]) / _DT_S,
        )
    decision = _decision_director.step(frame, _decision_state)
    ground_targets_with_ids = _ground_targets_with_ids(frame)
    _ground_search_mode = bool(ground_targets_with_ids and len(ground_targets_with_ids) <= 1)
    ground_by_id = {idx: pos for idx, pos in ground_targets_with_ids}
    ground_distances: list[tuple[int, tuple[float, float, float], float]] = []
    for idx, target in ground_targets_with_ids:
        dx = target[0] - pos[0]
        dy = target[1] - pos[1]
        dz = target[2] - pos[2]
        ground_distances.append((idx, target, math.sqrt(dx * dx + dy * dy + dz * dz)))
    ground_distances.sort(key=lambda item: item[2])

    focus_prev = _ground_focus_id
    if _ground_focus_id is not None and _ground_focus_id not in ground_by_id:
        _ground_focus_id = None
    if ground_distances:
        if _ground_focus_id is None:
            _ground_focus_id = ground_distances[0][0]
            _ground_focus_lock_until = frame + _GROUND_FOCUS_LOCK_FRAMES
        elif frame < _ground_focus_lock_until:
            pass
        else:
            current_dist = None
            for idx, _target, dist in ground_distances:
                if idx == _ground_focus_id:
                    current_dist = dist
                    break
            nearest_id, _nearest_target, nearest_dist = ground_distances[0]
            if current_dist is None:
                _ground_focus_id = nearest_id
                _ground_focus_lock_until = frame + _GROUND_FOCUS_LOCK_FRAMES
            elif (
                nearest_id != _ground_focus_id
                and nearest_dist <= current_dist * _GROUND_FOCUS_SWITCH_RATIO
            ):
                _ground_focus_id = nearest_id
                _ground_focus_lock_until = frame + _GROUND_FOCUS_LOCK_FRAMES
            else:
                focus_target = ground_by_id.get(_ground_focus_id)
                if focus_target is not None and not _target_ahead(
                    pos,
                    vel,
                    focus_target,
                    max_range=_ROCKET_FIRE_RANGE * 1.1,
                    min_dot=_GROUND_FIRE_CONE_DOT,
                ):
                    for idx, target, _dist in ground_distances:
                        if idx == _ground_focus_id:
                            continue
                        if _target_ahead(
                            pos,
                            vel,
                            target,
                            max_range=_ROCKET_FIRE_RANGE * 1.1,
                            min_dot=_GROUND_FIRE_CONE_DOT,
                        ):
                            _ground_focus_id = idx
                            _ground_focus_lock_until = frame + _GROUND_FOCUS_LOCK_FRAMES
                            break

    if focus_prev != _ground_focus_id:
        _primary_bomb_released = False

    primary_id: int | None = _ground_focus_id
    primary_target = ground_by_id.get(primary_id) if primary_id is not None else None
    secondary_id: int | None = None
    secondary_target = None
    for idx, target, _dist in ground_distances:
        if idx != primary_id:
            secondary_id = idx
            secondary_target = target
            break
    excluded_ids = {idx for idx in (primary_id, secondary_id) if idx is not None}
    other_ground_targets = [
        (idx, target) for idx, target, _dist in ground_distances if idx not in excluded_ids
    ]

    if primary_target is not None:
        primary_dx = primary_target[0] - pos[0]
        primary_dy = primary_target[1] - pos[1]
        primary_dist_xy = math.hypot(primary_dx, primary_dy)
        ahead_primary = _target_ahead(
            pos,
            vel,
            primary_target,
            max_range=_ROCKET_FIRE_RANGE * 1.4,
            min_dot=_GROUND_FIRE_CONE_DOT,
        )
        if primary_dist_xy > _GROUND_SEARCH_DIST or not ahead_primary:
            _ground_search_mode = True

    base_x, base_y, base_z = base_pos
    offset_x, offset_y = _search_offset
    search_gain = _SEARCH_OFFSET_GAIN
    search_decay = _SEARCH_OFFSET_DECAY
    search_max_ratio = _SEARCH_OFFSET_MAX_RATIO
    if _ground_search_mode:
        search_gain = 0.04
        search_decay = 0.05
        search_max_ratio = 0.25
    if _ground_search_mode and primary_target is not None:
        desired_x = primary_target[0] - base_x
        desired_y = primary_target[1] - base_y
        span_x = max(1.0, float(_cfg.TERRAIN_XMAX) - float(_cfg.TERRAIN_XMIN))
        span_y = max(1.0, float(_cfg.TERRAIN_YMAX) - float(_cfg.TERRAIN_YMIN))
        max_offset = search_max_ratio * min(span_x, span_y)
        dist = math.hypot(desired_x, desired_y)
        if dist > max_offset and dist > 1e-6:
            scale = max_offset / dist
            desired_x *= scale
            desired_y *= scale
        offset_x = _lerp(offset_x, desired_x, search_gain)
        offset_y = _lerp(offset_y, desired_y, search_gain)
    else:
        offset_x = _lerp(offset_x, 0.0, search_decay)
        offset_y = _lerp(offset_y, 0.0, search_decay)
    speed_xy = math.hypot(vel[0], vel[1])
    max_step = max(30.0, speed_xy * _DT_S * 0.20)
    delta_x = offset_x - _search_offset[0]
    delta_y = offset_y - _search_offset[1]
    delta_len = math.hypot(delta_x, delta_y)
    if delta_len > max_step and delta_len > 1e-6:
        scale = max_step / delta_len
        offset_x = _search_offset[0] + delta_x * scale
        offset_y = _search_offset[1] + delta_y * scale
    _search_offset = (offset_x, offset_y)
    pos = (base_x + offset_x, base_y + offset_y, base_z)
    pos = (
        min(max(pos[0], float(_cfg.TERRAIN_XMIN)), float(_cfg.TERRAIN_XMAX)),
        min(max(pos[1], float(_cfg.TERRAIN_YMIN)), float(_cfg.TERRAIN_YMAX)),
        pos[2],
    )
    ground_z = _sample_height(pos[0], pos[1], default=_cfg.TERRAIN_ZMIN)
    min_z = _coerce_float(ground_z, default=_cfg.TERRAIN_ZMIN) + _AIRCRAFT_TERRAIN_CLEARANCE
    if pos[2] < min_z:
        pos = (pos[0], pos[1], min_z)
    if prev_pos is not None:
        vel = (
            (pos[0] - prev_pos[0]) / _DT_S,
            (pos[1] - prev_pos[1]) / _DT_S,
            (pos[2] - prev_pos[2]) / _DT_S,
        )
    if _sim_vel_curr is not None:
        vel = _lerp3(_sim_vel_curr, vel, 0.25)

    RUNTIME.flight.plane_pos = pos
    RUNTIME.flight.plane_vel = vel

    _sim_pos_prev = prev_pos
    _sim_vel_prev = _sim_vel_curr
    _sim_pos_curr = pos
    _sim_vel_curr = vel

    bogie_pos = _bogies.get_position(frame)
    if bogie_pos is not None:
        _bogie_seen = True
    bogie_targets: list[tuple[str, tuple[float, float, float]]] = []
    bomb_only_id: int | None = None
    bomb_only_target: tuple[float, float, float] | None = None
    if len(ground_distances) >= 2:
        for idx, target, _dist in reversed(ground_distances):
            if idx != primary_id:
                bomb_only_id = idx
                bomb_only_target = target
                break
    ground_targets: list[tuple[str, tuple[float, float, float]]] = []
    if primary_target is not None and primary_id != bomb_only_id:
        ground_targets.append(("primary", primary_target))
    if secondary_target is not None and secondary_id != bomb_only_id:
        ground_targets.append(("secondary", secondary_target))
    for idx, target in other_ground_targets:
        if idx == bomb_only_id:
            continue
        ground_targets.append(("ground", target))
    bomb_targets: list[tuple[str, tuple[float, float, float]]] = []
    if bomb_only_target is not None:
        bomb_targets.append(("bomb_only", bomb_only_target))
    if primary_target is not None:
        bomb_targets.append(("primary", primary_target))
    if secondary_target is not None and secondary_id != bomb_only_id:
        bomb_targets.append(("secondary", secondary_target))
    for idx, target in other_ground_targets:
        if idx == bomb_only_id:
            continue
        bomb_targets.append(("ground", target))
    if bogie_pos is not None:
        bogie_targets.append(("bogie", bogie_pos))

    bogie_priority = False
    if bogie_pos is not None:
        if not ground_targets:
            bogie_priority = True
        else:
            dx = bogie_pos[0] - pos[0]
            dy = bogie_pos[1] - pos[1]
            dz = bogie_pos[2] - pos[2]
            bogie_dist = math.sqrt(dx * dx + dy * dy + dz * dz)
            if bogie_dist <= _BOGIE_PRIORITY_RANGE:
                bogie_priority = True

    ground_cone_dot = _GROUND_SEARCH_CONE_DOT if _ground_search_mode else _GROUND_FIRE_CONE_DOT
    if bogie_priority:
        bullet_choice = _first_target_ahead(
            bogie_targets,
            pos,
            vel,
            max_range=_BULLET_FIRE_RANGE,
            min_dot=_FIRE_CONE_DOT,
        )
        if bullet_choice is None:
            bullet_choice = _first_target_ahead(
                ground_targets,
                pos,
                vel,
                max_range=_BULLET_FIRE_RANGE,
                min_dot=ground_cone_dot,
            )
        rocket_choice = _first_target_ahead(
            bogie_targets,
            pos,
            vel,
            max_range=_ROCKET_FIRE_RANGE,
            min_dot=_FIRE_CONE_DOT,
        )
        if rocket_choice is None:
            rocket_choice = _first_target_ahead(
                ground_targets,
                pos,
                vel,
                max_range=_ROCKET_FIRE_RANGE,
                min_dot=ground_cone_dot,
            )
    else:
        bullet_choice = _first_target_ahead(
            ground_targets,
            pos,
            vel,
            max_range=_BULLET_FIRE_RANGE,
            min_dot=ground_cone_dot,
        )
        if bullet_choice is None:
            bullet_choice = _first_target_ahead(
                bogie_targets,
                pos,
                vel,
                max_range=_BULLET_FIRE_RANGE,
                min_dot=_FIRE_CONE_DOT,
            )
        rocket_choice = _first_target_ahead(
            ground_targets,
            pos,
            vel,
            max_range=_ROCKET_FIRE_RANGE,
            min_dot=ground_cone_dot,
        )
        if rocket_choice is None:
            rocket_choice = _first_target_ahead(
                bogie_targets,
                pos,
                vel,
                max_range=_ROCKET_FIRE_RANGE,
                min_dot=_FIRE_CONE_DOT,
            )
    if bogie_priority and bogie_pos is not None:
        if bullet_choice is None:
            bullet_choice = ("bogie", bogie_pos)
        if rocket_choice is None:
            rocket_choice = ("bogie", bogie_pos)
    target_kind_bullet = bullet_choice[0] if bullet_choice else None
    target_bullet = bullet_choice[1] if bullet_choice else None
    target_kind_rocket = rocket_choice[0] if rocket_choice else None
    target_rocket = rocket_choice[1] if rocket_choice else None

    bullet_dist = None
    if target_bullet is not None:
        dx = target_bullet[0] - pos[0]
        dy = target_bullet[1] - pos[1]
        dz = target_bullet[2] - pos[2]
        bullet_dist = math.sqrt(dx * dx + dy * dy + dz * dz)

    active_bullets = _safe_len(RUNTIME.active_bullets)
    active_rockets = _safe_len(RUNTIME.active_rockets)
    active_bombs = _safe_len(RUNTIME.active_bombs)
    has_projectiles = (active_bullets + active_rockets + active_bombs) > 0

    tactic = _ground_tactic or "mixed"
    if bogie_pos is None and ground_targets:
        tactic = "mixed"
    if tactic == "rocket" and _decision_state.rockets_remaining <= 0:
        tactic = "mixed"
    if tactic == "strafe" and _decision_state.bullets_remaining <= 0:
        tactic = "mixed"
    primary_drop_ok = primary_target is not None and _should_drop_bomb(pos, vel, primary_target)
    allow_bullets = False
    if target_kind_bullet == "bogie":
        allow_bullets = True
    elif target_kind_bullet in {"secondary", "ground"}:
        if tactic in {"strafe", "mixed"}:
            allow_bullets = True
        elif tactic == "rocket" and bullet_dist is not None:
            allow_bullets = bullet_dist <= (_BULLET_FIRE_RANGE * 0.70)
    elif target_kind_bullet == "primary":
        allow_bullets = _primary_bomb_released or _decision_state.bombs_remaining <= 0 or not primary_drop_ok

    allow_rockets = False
    if target_kind_rocket == "bogie":
        allow_rockets = True
    elif target_kind_rocket in {"secondary", "ground"}:
        allow_rockets = tactic in {"rocket", "mixed"} or not allow_bullets
    elif target_kind_rocket == "primary":
        allow_rockets = _primary_bomb_released or _decision_state.bombs_remaining <= 0 or not primary_drop_ok

    bomb_choice = _first_target_ahead(
        bomb_targets,
        pos,
        vel,
        max_range=_BOMB_DROP_MAX_ALONG * 1.1,
        min_dot=_GROUND_FIRE_CONE_DOT,
    )
    bomb_target = bomb_choice[1] if bomb_choice else (bomb_only_target or primary_target)
    if bomb_target is None and secondary_target is not None and _decision_state.bombs_remaining > 0:
        bomb_target = secondary_target
    if bomb_target is None and other_ground_targets and _decision_state.bombs_remaining > 0:
        bomb_target = other_ground_targets[0][1]
    phase = (
        _decision_state.phase_table[frame]
        if 0 <= frame < len(_decision_state.phase_table)
        else "Unknown"
    )
    drop_candidate = bomb_target is not None and _should_drop_bomb(pos, vel, bomb_target)
    bomb_phase_ok = True
    bombing_bounds = slice_map.get("Bombing")
    bombing_start = None
    bombing_pad = 0
    if bombing_bounds is not None:
        bombing_start, bombing_end = bombing_bounds
        bombing_start = int(bombing_start)
        bombing_end = int(bombing_end)
        bombing_len = max(0, bombing_end - bombing_start)
        bombing_pad = max(_BOMB_DROP_EARLY_FRAMES, int(bombing_len * 0.15))
        if bombing_len:
            bombing_pad = min(bombing_pad, max(0, bombing_len - 1))
        bomb_phase_ok = phase == "Bombing"
    target_under = False
    if bomb_target is not None:
        target_under = _target_under(
            pos,
            bomb_target,
            max_lateral=_BOMB_DROP_UNDER_LATERAL,
            min_alt=_BOMB_DROP_MIN_ALT,
        )
    if (
        not bomb_phase_ok
        and bombing_start is not None
        and frame >= bombing_start
        and frame <= (bombing_start + _BOMB_DROP_EARLY_FRAMES)
        and bomb_target is not None
        and target_under
    ):
        bomb_phase_ok = True
    if bomb_phase_ok and bombing_start is not None:
        if frame < (bombing_start + bombing_pad) and not target_under:
            bomb_phase_ok = False
    if not bomb_phase_ok and drop_candidate and frame >= _BOMB_MIN_FRAME:
        bomb_phase_ok = True
    drop_ok = drop_candidate and bomb_phase_ok
    if not drop_ok and bomb_phase_ok and target_under:
        drop_ok = True
    force_bomb = (
        bomb_target is not None
        and bomb_target == primary_target
        and drop_ok
        and _decision_state.bombs_remaining > 0
    )
    do_drop_bomb = decision.drop_bomb or force_bomb
    if (
        not do_drop_bomb
        and drop_ok
        and _decision_state.bombs_remaining > 0
        and frame >= _decision_state.bomb_cooldown_until
    ):
        do_drop_bomb = True
        force_bomb = True
    if do_drop_bomb and active_bombs >= _MAX_ACTIVE_BOMBS:
        do_drop_bomb = False
    if do_drop_bomb and drop_ok:
        bombs_schedule_release(frame)
        if bomb_target == primary_target:
            _primary_bomb_released = True
        if force_bomb and not decision.drop_bomb:
            _decision_state.bombs_remaining = max(0, _decision_state.bombs_remaining - 1)
            cooldown = _rand_range(
                _decision_director._rng,  # type: ignore[attr-defined]
                _decision_director._config.bomb_cooldown,  # type: ignore[attr-defined]
            )
            _decision_state.bomb_cooldown_until = frame + max(1, cooldown)
    elif decision.drop_bomb:
        _decision_state.bombs_remaining += 1
        _decision_state.bomb_cooldown_until = frame

    do_launch_rocket = False
    if allow_rockets and target_rocket is not None:
        do_launch_rocket = decision.launch_rocket
        if (
            not do_launch_rocket
            and _decision_state.rockets_remaining > 0
            and frame >= _decision_state.rocket_cooldown_until
            and (frame - _last_rocket_fire) >= _FORCE_ROCKET_GAP
        ):
            do_launch_rocket = True
            if not decision.launch_rocket:
                _decision_state.rockets_remaining = max(0, _decision_state.rockets_remaining - 1)
                cooldown = _rand_range(
                    _decision_director._rng,  # type: ignore[attr-defined]
                    _decision_director._config.rocket_cooldown,  # type: ignore[attr-defined]
                )
                _decision_state.rocket_cooldown_until = frame + max(1, cooldown)
    if do_launch_rocket and active_rockets >= _MAX_ACTIVE_ROCKETS:
        do_launch_rocket = False
    if do_launch_rocket:
        _rockets.schedule_launch(frame)
        _last_rocket_fire = frame
    elif decision.launch_rocket:
        _decision_state.rockets_remaining += 1
        _decision_state.rocket_cooldown_until = frame

    do_fire_bullets = False
    forced_bullets = False
    if allow_bullets and target_bullet is not None:
        do_fire_bullets = decision.fire_bullets
        if (
            not do_fire_bullets
            and _decision_state.bullets_remaining > 0
            and (frame - _last_bullet_fire) >= _FORCE_BULLET_GAP
        ):
            do_fire_bullets = True
            forced_bullets = True
            if not decision.fire_bullets:
                _decision_state.bullets_remaining = max(0, _decision_state.bullets_remaining - 1)
                _decision_state.next_bullet_frame = frame + _FORCED_BULLET_SPACING
    if do_fire_bullets and active_bullets >= _MAX_ACTIVE_BULLETS:
        do_fire_bullets = False
        forced_bullets = False
    if decision.fire_bullets and not do_fire_bullets:
        _decision_state.bullets_remaining = min(
            _decision_state.bullets_remaining + 1,
            _decision_director._config.ammo_bursts,  # type: ignore[attr-defined]
        )
        _decision_state.next_bullet_frame = frame
    muzzle_pos = _weapon_origin(pos, vel)
    aim_target = None
    if do_launch_rocket and target_rocket is not None:
        aim_target = target_rocket
    elif do_fire_bullets and target_bullet is not None:
        aim_target = target_bullet
    elif target_rocket is not None:
        aim_target = target_rocket
    elif target_bullet is not None:
        aim_target = target_bullet
    aim_vel = vel
    if _cfg.AIM_ASSIST and aim_target is not None:
        aim_vel = _aim_velocity(pos, vel, aim_target)
    if do_fire_bullets:
        burst = _cfg.BULLET_BURST
        if forced_bullets:
            burst = max(burst, _FORCED_BULLET_BURST)
        remaining_slots = max(0, _MAX_ACTIVE_BULLETS - active_bullets)
        if remaining_slots <= 0:
            burst = 0
        else:
            burst = min(burst, remaining_slots)
        if burst <= 0:
            do_fire_bullets = False
        else:
            _bullets.spawn(frame, muzzle_pos, aim_vel, ax, bullets=burst)
            _last_bullet_fire = frame

    # projectiles
    if profile_enabled:
        start = time.perf_counter()
        _rockets.step(frame, muzzle_pos, aim_vel, ax)
        timings["rockets_ms"] = (time.perf_counter() - start) * 1_000
    else:
        _rockets.step(frame, muzzle_pos, aim_vel, ax)

    if profile_enabled:
        start = time.perf_counter()
        _bullets.update(frame, ax)
        timings["bullets_ms"] = (time.perf_counter() - start) * 1_000
    else:
        _bullets.update(frame, ax)

    if profile_enabled:
        start = time.perf_counter()
        bombs_step(frame, pos, vel, ax)
        timings["bombs_ms"] = (time.perf_counter() - start) * 1_000
    else:
        bombs_step(frame, pos, vel, ax)

    _check_aircraft_hits(frame, pos)

    if profile_enabled:
        timings["projectiles_ms"] = (
            timings["rockets_ms"] + timings["bullets_ms"] + timings["bombs_ms"]
        )

    # AI + VFX
    bogie_frame = frame
    if n_frames > 0:
        bogie_frame = min(max(frame, 0), n_frames - 1)
    if profile_enabled:
        start = time.perf_counter()
        _bogies.update(bogie_frame)
        timings["bogies_ms"] = (time.perf_counter() - start) * 1_000
    else:
        _bogies.update(bogie_frame)

    do_ground = _GROUND_UPDATE_STRIDE <= 1 or (frame % _GROUND_UPDATE_STRIDE == 0)
    if profile_enabled:
        start = time.perf_counter()
        if do_ground:
            _ground.update(frame, pos[0], pos[1])
        if has_projectiles:
            _ground.check_hits(frame, advance=not do_ground)
        timings["ground_ms"] = (time.perf_counter() - start) * 1_000
    else:
        if do_ground:
            _ground.update(frame, pos[0], pos[1])
        if has_projectiles:
            _ground.check_hits(frame, advance=not do_ground)

    has_explosions = _explosion_count() > 0
    if profile_enabled:
        if has_explosions:
            start = time.perf_counter()
            update_explosion()
            timings["explosions_ms"] = (time.perf_counter() - start) * 1_000
        else:
            timings["explosions_ms"] = 0.0
    elif has_explosions:
        update_explosion()

    has_parachutes = _parachute_count() > 0
    if profile_enabled:
        if has_parachutes:
            start = time.perf_counter()
            update_parachute()
            timings["parachutes_ms"] = (time.perf_counter() - start) * 1_000
        else:
            timings["parachutes_ms"] = 0.0
    elif has_parachutes:
        update_parachute()

    if profile_enabled:
        timings["vfx_ai_ms"] = (
            timings["bogies_ms"]
            + timings["ground_ms"]
            + timings["explosions_ms"]
            + timings["parachutes_ms"]
        )
    return timings

# ───────────────────────── 4 · frame loop ─────────────────────────────────
def _update(frame: int) -> Tuple[Artist, ...]:
    if ax is None:
        return tuple()

    global _last_update_start, _last_update_frame, _last_update_ms
    global _sim_frame, _combat_tick, _ground_tick, _loop_mode
    global _celebration_active, _celebration_hold_left, _celebration_tick
    global _sim_started, _sim_accum_ms, _sim_last_tick, _sim_done, _finish_after_render
    global _sim_pos_prev, _sim_pos_curr, _sim_vel_prev, _sim_vel_curr
    global _simulation, _loop_reset_pending, _hold_dogfight_bounds, _hold_ground_bounds

    render_frame = frame
    frame_start = time.perf_counter()
    profile_enabled = False
    timings = {} if profile_enabled else _EMPTY_TIMINGS
    if profile_enabled and _last_update_start is not None:
        timings["interval_ms"] = (frame_start - _last_update_start) * 1_000
    _last_update_start = frame_start
    _last_update_frame = render_frame

    if _sim_done:
        return tuple()

    sim_steps = 1
    sim_alpha = 0.0
    forced_step = False
    if not _sim_started:
        _sim_started = True
        _sim_last_tick = frame_start
        _sim_accum_ms = 0.0
    elif SIM_REALTIME:
        if _sim_last_tick is None:
            _sim_last_tick = frame_start
        elapsed_ms = (frame_start - _sim_last_tick) * 1_000
        _sim_last_tick = frame_start
        _sim_accum_ms += elapsed_ms
        sim_steps = int(_sim_accum_ms // SIM_DT_MS)
        if sim_steps < 1:
            sim_steps = 1
            forced_step = True
            _sim_accum_ms = 0.0
        if sim_steps > SIM_MAX_STEPS:
            sim_steps = SIM_MAX_STEPS
            _sim_accum_ms = 0.0
        else:
            _sim_accum_ms = max(0.0, _sim_accum_ms - (SIM_DT_MS * sim_steps))
        sim_alpha = min(1.0, max(0.0, _sim_accum_ms / SIM_DT_MS))
        if forced_step:
            sim_alpha = 1.0
    else:
        _sim_last_tick = frame_start
        _sim_accum_ms = 0.0

    if not SIM_REALTIME:
        sim_steps = 1
        sim_alpha = 1.0

    dogfight_bounds = _dogfight_bounds()
    victory_bounds = _victory_bounds()
    ground_attack_bounds = _ground_attack_bounds()
    ground_search_bounds = _ground_search_bounds()
    ground_bounds = ground_search_bounds if _ground_search_mode else ground_attack_bounds
    active_dogfight_bounds = _hold_dogfight_bounds or dogfight_bounds
    active_ground_bounds = _hold_ground_bounds or ground_bounds
    bogies_alive = _bogies.is_alive()
    bogie_pending = _bogie_expected and not _bogie_seen
    ground_alive = _ground.has_live_targets()
    hold_for_enemies = ground_alive or bogies_alive or bogie_pending
    if hold_for_enemies and _celebration_active:
        _celebration_active = False
        _celebration_hold_left = 0
        _celebration_tick = None
        _ground_tick = None
        _loop_mode = None
        _hold_dogfight_bounds = None
        _hold_ground_bounds = None
        if dogfight_bounds is not None and _sim_frame < dogfight_bounds[0]:
            _sim_frame = dogfight_bounds[0]
            _reset_interpolation()
    if not hold_for_enemies and not _celebration_active and victory_bounds is not None:
        _celebration_active = True
        _celebration_hold_left = _CELEBRATION_HOLD_FRAMES
        _celebration_tick = None
        _combat_tick = None
        _ground_tick = None
        _loop_mode = None
        _hold_dogfight_bounds = None
        _hold_ground_bounds = None
    bogie_holds_ground = bogie_pending and active_ground_bounds is not None
    hold_active = (
        bogies_alive
        and not ground_alive
        and not bogie_holds_ground
        and not _celebration_active
        and active_dogfight_bounds is not None
        and (_combat_tick is not None or _sim_frame >= active_dogfight_bounds[0])
    )
    ground_hold_active = (
        (ground_alive or bogie_holds_ground)
        and not _celebration_active
        and active_ground_bounds is not None
        and (_ground_tick is not None or _sim_frame >= active_ground_bounds[0])
    )
    if hold_active and _loop_mode != "dogfight":
        _loop_mode = "dogfight"
        _hold_dogfight_bounds = active_dogfight_bounds
        _hold_ground_bounds = None
        _combat_tick = None
        _ground_tick = None
        _reset_interpolation()
    elif ground_hold_active and _loop_mode != "ground":
        _loop_mode = "ground"
        _hold_ground_bounds = active_ground_bounds
        _hold_dogfight_bounds = None
        _ground_tick = None
        _combat_tick = None
        _reset_interpolation()
    elif not hold_active and not ground_hold_active and _loop_mode is not None:
        _loop_mode = None
        _hold_dogfight_bounds = None
        _hold_ground_bounds = None
        _combat_tick = None
        _ground_tick = None
    celebration_hold_active = (
        _celebration_active
        and victory_bounds is not None
        and _sim_frame >= victory_bounds[0]
        and _celebration_hold_left > 0
    )
    loop_guard = hold_active or ground_hold_active or celebration_hold_active

    remaining = n_frames - _sim_frame
    if remaining <= 0 and not loop_guard:
        if _repeat_enabled():
            _reset_loop_flags()
            _loop_reset_pending = True
            _sim_frame = 0
            _sim_started = False
            _sim_accum_ms = 0.0
            _sim_last_tick = frame_start
            return tuple()
        _sim_done = True
        if anim is not None:
            anim.event_source.stop()
        _finish_after_render = True
        return tuple()
    if sim_steps > remaining and not loop_guard:
        sim_steps = remaining

    force_end = False
    for _ in range(sim_steps):
        step_frame = _sim_frame
        advance_frame = True
        if hold_active and active_dogfight_bounds is not None:
            start, end, _span, _period = active_dogfight_bounds
            loop_len = max(1, end - start)
            if _combat_tick is None:
                init_tick = _sim_frame - start
                if init_tick < 0:
                    init_tick = 0
                elif init_tick >= loop_len:
                    init_tick = loop_len - 1
                _combat_tick = init_tick
                _reset_interpolation()
                _decision_director.rearm(_decision_state, frame=step_frame)
            step_frame, wrapped = _pingpong_loop_frame(
                _combat_tick,
                start=start,
                end=end,
            )
            if wrapped:
                _decision_director.rearm(_decision_state, frame=step_frame)
            _combat_tick += 1
            advance_frame = False
        elif ground_hold_active and active_ground_bounds is not None:
            start, end, _span, _period = active_ground_bounds
            loop_len = max(1, end - start)
            if _ground_tick is None:
                init_tick = _sim_frame - start
                if init_tick < 0:
                    init_tick = 0
                elif init_tick >= loop_len:
                    init_tick = loop_len - 1
                _ground_tick = init_tick
                _reset_interpolation()
                _decision_director.rearm(_decision_state, frame=step_frame)
            step_frame, wrapped = _pingpong_loop_frame(
                _ground_tick,
                start=start,
                end=end,
            )
            if wrapped:
                _decision_director.rearm(_decision_state, frame=step_frame)
            _ground_tick += 1
            advance_frame = False
        elif _celebration_active and victory_bounds is not None and _sim_frame >= victory_bounds[0]:
            start, end = victory_bounds
            loop_len = max(1, end - start)
            if _celebration_tick is None:
                init_tick = _sim_frame - start
                if init_tick < 0:
                    init_tick = 0
                elif init_tick >= loop_len:
                    init_tick = loop_len - 1
                _celebration_tick = init_tick
            step_frame = start + min(_celebration_tick, loop_len - 1)
            _celebration_tick += 1
            if _celebration_hold_left > 0:
                _celebration_hold_left -= 1
                if _celebration_hold_left <= 0:
                    force_end = True
            advance_frame = False
        if _simulation is None:
            _simulation = Simulation(step_callback=_step_sim)
        step_timings = _simulation.step(step_frame)
        if advance_frame:
            _sim_frame += 1
            if _sim_frame > n_frames:
                _sim_frame = n_frames
        else:
            _sim_frame = step_frame
        if profile_enabled:
            for key, value in step_timings.items():
                timings[key] = timings.get(key, 0.0) + value
        if force_end:
            break

    if force_end:
        _celebration_active = False
        _celebration_tick = None
        _sim_frame = n_frames

    if _sim_pos_curr is not None:
        if _sim_pos_prev is None:
            interp_pos = _sim_pos_curr
        else:
            interp_pos = _lerp3(_sim_pos_prev, _sim_pos_curr, sim_alpha)
        if _sim_vel_curr is None:
            interp_vel = (0.0, 0.0, 0.0)
        elif _sim_vel_prev is None:
            interp_vel = _sim_vel_curr
        else:
            interp_vel = _lerp3(_sim_vel_prev, _sim_vel_curr, sim_alpha)
        if _should_update_camera(render_frame):
            center_x, center_y, center_z = _camera_center(interp_pos, interp_vel)
            _set_scene_bounds(center_x, center_y, center_z)
            _apply_scene_limits()
            _update_camera_view(interp_vel)
        if profile_enabled:
            start = time.perf_counter()
            step_aircraft(interp_pos, interp_vel)
            timings["aircraft_ms"] = (time.perf_counter() - start) * 1_000
        else:
            step_aircraft(interp_pos, interp_vel)

    bogies_alive = _bogies.is_alive()
    bogie_pending = _bogie_expected and not _bogie_seen
    ground_alive = _ground.has_live_targets()
    active_dogfight_bounds = _hold_dogfight_bounds or dogfight_bounds
    active_ground_bounds = _hold_ground_bounds or ground_bounds
    bogie_holds_ground = bogie_pending and active_ground_bounds is not None
    hold_active = (
        bogies_alive
        and not ground_alive
        and not bogie_holds_ground
        and not _celebration_active
        and active_dogfight_bounds is not None
        and (_combat_tick is not None or _sim_frame >= active_dogfight_bounds[0])
    )
    ground_hold_active = (
        (ground_alive or bogie_holds_ground)
        and not _celebration_active
        and active_ground_bounds is not None
        and (_ground_tick is not None or _sim_frame >= active_ground_bounds[0])
    )
    if hold_active and _loop_mode != "dogfight":
        _loop_mode = "dogfight"
        _hold_dogfight_bounds = active_dogfight_bounds
        _hold_ground_bounds = None
        _combat_tick = None
        _ground_tick = None
        _reset_interpolation()
    elif ground_hold_active and _loop_mode != "ground":
        _loop_mode = "ground"
        _hold_ground_bounds = active_ground_bounds
        _hold_dogfight_bounds = None
        _ground_tick = None
        _combat_tick = None
        _reset_interpolation()
    elif not hold_active and not ground_hold_active and _loop_mode is not None:
        _loop_mode = None
        _hold_dogfight_bounds = None
        _hold_ground_bounds = None
        _combat_tick = None
        _ground_tick = None
    celebration_hold_active = (
        _celebration_active
        and victory_bounds is not None
        and _sim_frame >= victory_bounds[0]
        and _celebration_hold_left > 0
    )
    loop_guard = hold_active or ground_hold_active or celebration_hold_active
    if _sim_frame >= n_frames and not loop_guard:
        if _repeat_enabled():
            _reset_loop_flags()
            _loop_reset_pending = True
            _sim_frame = 0
            _sim_started = False
            _sim_accum_ms = 0.0
            _sim_last_tick = frame_start
        else:
            _sim_done = True
            if anim is not None:
                anim.event_source.stop()
            _finish_after_render = True


    return tuple()

# ───────────────────────── 5 · driver ─────────────────────────────────────
def _repeat_enabled() -> bool:
    return os.environ.get("WARBITS_LOOP", "1").lower() not in {"0", "false", "off", "no"}


def _ensure_animation() -> FuncAnimation:
    global fig, ax, anim, _keep_ref, _hud_text, _adaptive, _adaptive_lod
    global _terrain_surface, _terrain_base, _terrain_lod
    global _startup_seed
    if anim is not None:
        return anim

    fig, ax = _cfg.create_scene_canvas()
    register_axes(ax)
    _register_para_axes(ax)
    _register_ac_axes(ax)
    _terrain_base = (_cfg.TERRAIN_STEP, _cfg.TERRAIN_RCOUNT, _cfg.TERRAIN_CCOUNT)
    if _startup_seed is None:
        _startup_seed = (
            _cfg.SCENARIO_SEED
            if _cfg.SCENARIO_SEED is not None
            else secrets.randbits(32)
        )
    if _terrain_profile is None or _terrain_seed is None:
        _set_terrain_context(_startup_seed)
    if flight_x.size:
        _set_scene_bounds(float(flight_x[0]), float(flight_y[0]), float(flight_z[0]))
    step, rcount, ccount = _clamp_grid(*_terrain_base)
    _terrain_lod = (step, rcount, ccount, _terrain_profile, _terrain_seed)
    _, _, _, _terrain_surface = _draw_terrain(
        ax,
        step=step,
        rcount=rcount,
        ccount=ccount,
        profile=_terrain_profile,
        seed=_terrain_seed,
        return_surface=True,
    )
    _apply_scene_limits()

    _ground.init(ax)
    _bogies.init(ax, flight_x, flight_y, flight_z, slice_map)

    if _cfg.ADAPT_RENDER and (not _cfg.FULLSCREEN or _cfg.ADAPT_FULLSCREEN):
        _adaptive = _AdaptiveScaler(
            fig,
            target_ms=_cfg.ADAPT_TARGET_MS,
            window=_cfg.ADAPT_WINDOW,
            step=_cfg.ADAPT_STEP,
            min_scale=_cfg.ADAPT_MIN_SCALE,
            max_scale=_cfg.ADAPT_MAX_SCALE,
            cooldown=_cfg.ADAPT_COOLDOWN,
            allow_upscale=_cfg.ADAPT_UPSCALE,
            resize_window=not _cfg.FULLSCREEN,
        )
    if _cfg.ADAPT_LOD:
        _adaptive_lod = _AdaptiveLOD(
            target_ms=_cfg.ADAPT_TARGET_MS,
            window=_cfg.ADAPT_WINDOW,
            step=_cfg.ADAPT_STEP,
            min_scale=_cfg.ADAPT_MIN_SCALE,
            max_scale=_cfg.ADAPT_MAX_SCALE,
            cooldown=_cfg.ADAPT_COOLDOWN,
            allow_upscale=_cfg.ADAPT_UPSCALE,
            base_step=_terrain_base[0] if _terrain_base else _cfg.TERRAIN_STEP,
            base_rcount=_terrain_base[1] if _terrain_base else _cfg.TERRAIN_RCOUNT,
            base_ccount=_terrain_base[2] if _terrain_base else _cfg.TERRAIN_CCOUNT,
        )

    try:
        fig.canvas.mpl_connect("draw_event", _on_draw)
    except Exception:
        pass

    anim = FuncAnimation(
        fig,
        _update,
        frames=itertools.count(),
        interval=FRAME_INTERVAL_MS,
        blit=False,
        repeat=False,
        cache_frame_data=False,
    )
    _keep_ref = anim  # prevent early GC
    return anim


def ensure_animation() -> FuncAnimation:
    return _ensure_animation()


def run_animation() -> None:
    _ensure_animation()
    import matplotlib.pyplot as plt
    plt.show()


if __name__ == "__main__":
    run_animation()


# ───────────────────────── profiling support ───────────────────────────────
def _on_draw(event: Any) -> None:
    global _finish_after_render, _adapt_warmup_remaining
    if _last_update_start is None or _last_update_frame is None:
        return
    render_ms = (time.perf_counter() - _last_update_start) * 1_000
    if _last_update_ms is not None:
        render_ms = max(0.0, render_ms - _last_update_ms)
    if _adapt_warmup_remaining > 0:
        _adapt_warmup_remaining -= 1
    else:
        if _adaptive is not None:
            _adaptive.record(render_ms)
        if _adaptive_lod is not None and not _cfg.TERRAIN_LOCK_LOD:
            _adaptive_lod.record(render_ms)
    if fig is not None:
        _guard_fullscreen(fig)
    if _finish_after_render:
        _finish_after_render = False


def _guard_fullscreen(fig: Any) -> None:
    global _last_fullscreen_guard
    if not _cfg.FULLSCREEN:
        return
    now = time.perf_counter()
    if _last_fullscreen_guard is not None and (now - _last_fullscreen_guard) < 1.0:
        return
    manager = getattr(fig.canvas, "manager", None)
    if manager is None:
        return
    backend = ""
    try:
        import matplotlib
        backend = matplotlib.get_backend().lower()
    except Exception:
        backend = ""
    is_full: bool | None = None
    window_size: tuple[int, int] | None = None
    try:
        if "qt" in backend:
            window = getattr(manager, "window", None)
            if window is not None:
                check = getattr(window, "isFullScreen", None)
                if callable(check):
                    is_full = bool(check())
                try:
                    size = window.size()
                    window_size = (int(size.width()), int(size.height()))
                except Exception:
                    window_size = None
        elif "tkagg" in backend:
            window = getattr(manager, "window", None)
            if window is not None:
                check = getattr(window, "attributes", None)
                if callable(check):
                    is_full = bool(check("-fullscreen"))
                try:
                    window_size = (int(window.winfo_width()), int(window.winfo_height()))
                except Exception:
                    window_size = None
        elif "wx" in backend:
            frame = getattr(manager, "frame", None)
            if frame is not None:
                check = getattr(frame, "IsFullScreen", None)
                if callable(check):
                    is_full = bool(check())
                try:
                    size = frame.GetSize()
                    window_size = (int(size.GetWidth()), int(size.GetHeight()))
                except Exception:
                    window_size = None
    except Exception:
        is_full = None
    if is_full is True:
        _last_fullscreen_guard = now
        return

    ratio_ok: bool | None = None
    try:
        screen_w = max(1, int(_cfg.SCREEN_WIDTH_PX))
        screen_h = max(1, int(_cfg.SCREEN_HEIGHT_PX))
        if window_size is not None:
            window_w = max(1, window_size[0])
            window_h = max(1, window_size[1])
            ratio = min(window_w / screen_w, window_h / screen_h)
            ratio_ok = ratio >= 0.9
        else:
            width_px, height_px = fig.canvas.get_width_height()
            ratio = min(width_px / screen_w, height_px / screen_h)
            dpr = _coerce_float(getattr(fig.canvas, "device_pixel_ratio", 0.0))
            if dpr > 0.0:
                ratio = max(
                    ratio,
                    min((width_px / dpr) / screen_w, (height_px / dpr) / screen_h),
                )
            scale_hint = _coerce_float(getattr(_cfg, "CANVAS_SCALE", 1.0), default=1.0)
            if scale_hint <= 0.0:
                scale_hint = 1.0
            scale_hint = min(1.0, max(0.1, scale_hint))
            ratio_ok = ratio >= (0.9 * scale_hint)
    except Exception:
        ratio_ok = None
    if is_full is None:
        if ratio_ok is None:
            return
        is_full = ratio_ok
    if is_full:
        return
    _last_fullscreen_guard = now
    try:
        _cfg.make_fullscreen(fig)
    except Exception:
        return
    try:
        fig.subplots_adjust(left=0, right=1, bottom=0, top=1)
    except Exception:
        pass
    try:
        fig.canvas.draw_idle()
    except Exception:
        pass


class _AdaptiveScaler:
    """Adjust canvas scale to keep render time near target."""

    def __init__(
        self,
        fig: Any,
        *,
        target_ms: float,
        window: int,
        step: float,
        min_scale: float,
        max_scale: float,
        cooldown: float,
        allow_upscale: bool,
        resize_window: bool,
    ) -> None:
        self._fig = fig
        self._target_ms = max(1.0, float(target_ms))
        self._step = max(0.01, float(step))
        self._min_scale = max(0.1, float(min_scale))
        self._max_scale = max(self._min_scale, float(max_scale))
        self._allow_upscale = allow_upscale
        self._resize_window = resize_window
        self._cooldown = max(0.1, float(cooldown))
        self._last_adjust = 0.0
        window_size = max(5, int(window))
        self._window_maxlen: int = window_size
        self._window: Deque[float] = deque(maxlen=window_size)
        try:
            self._base_size = tuple(self._fig.get_size_inches())
        except Exception:
            self._base_size = (1.0, 1.0)
        try:
            self._base_dpi = float(self._fig.get_dpi())
        except Exception:
            self._base_dpi = 100.0
        self._scale = 1.0

    def record(self, render_ms: float) -> None:
        if render_ms <= 0.0:
            return
        self._window.append(render_ms)
        window_list = [float(v) for v in self._window]
        if len(window_list) < self._window_maxlen:
            return
        now = time.perf_counter()
        if (now - self._last_adjust) < self._cooldown:
            return
        avg = sum(window_list) / len(window_list)
        high = self._target_ms * 1.05
        low = self._target_ms * 0.75
        if avg > high and self._scale > self._min_scale:
            self._apply(max(self._min_scale, self._scale - self._step), now)
        elif self._allow_upscale and avg < low and self._scale < self._max_scale:
            self._apply(min(self._max_scale, self._scale + self._step), now)

    def _apply(self, new_scale: float, now: float) -> None:
        if abs(new_scale - self._scale) < 1e-6:
            return
        self._scale = new_scale
        self._last_adjust = now
        if self._resize_window:
            try:
                w, h = self._base_size
                self._fig.set_size_inches(w * new_scale, h * new_scale, forward=True)
                if hasattr(self._fig, "canvas"):
                    try:
                        self._fig.canvas.draw_idle()
                    except Exception:
                        pass
            except Exception:
                pass
            return
        try:
            new_dpi = max(10.0, self._base_dpi * new_scale)
            self._fig.set_dpi(new_dpi)
            if hasattr(self._fig, "canvas"):
                try:
                    self._fig.canvas.draw_idle()
                except Exception:
                    pass
        except Exception:
            pass


class _AdaptiveLOD:
    """Adjust terrain resolution to keep render time near target."""

    def __init__(
        self,
        *,
        target_ms: float,
        window: int,
        step: float,
        min_scale: float,
        max_scale: float,
        cooldown: float,
        allow_upscale: bool,
        base_step: int,
        base_rcount: int,
        base_ccount: int,
    ) -> None:
        self._target_ms = max(1.0, float(target_ms))
        self._step = max(0.01, float(step))
        self._min_scale = max(0.1, float(min_scale))
        self._max_scale = max(self._min_scale, float(max_scale))
        self._allow_upscale = allow_upscale
        self._cooldown = max(0.1, float(cooldown))
        self._last_adjust = 0.0
        window_size = max(5, int(window))
        self._window_maxlen: int = window_size
        self._window: Deque[float] = deque(maxlen=window_size)
        self._scale = 1.0
        self._base_step = max(2, int(base_step))
        self._base_rcount = max(2, int(base_rcount))
        self._base_ccount = max(2, int(base_ccount))

    def record(self, render_ms: float) -> None:
        if render_ms <= 0.0:
            return
        self._window.append(render_ms)
        if len(self._window) < self._window_maxlen:
            return
        now = time.perf_counter()
        if (now - self._last_adjust) < self._cooldown:
            return
        avg = sum(self._window) / len(self._window)
        high = self._target_ms * 1.05
        low = self._target_ms * 0.75
        if avg > high and self._scale > self._min_scale:
            self._apply(max(self._min_scale, self._scale - self._step), now)
        elif self._allow_upscale and avg < low and self._scale < self._max_scale:
            self._apply(min(self._max_scale, self._scale + self._step), now)

    def _apply(self, new_scale: float, now: float) -> None:
        if abs(new_scale - self._scale) < 1e-6:
            return
        self._scale = new_scale
        self._last_adjust = now
        step = int(round(self._base_step * new_scale))
        rcount = int(round(self._base_rcount * new_scale))
        ccount = int(round(self._base_ccount * new_scale))
        _rebuild_terrain(step, rcount, ccount)


