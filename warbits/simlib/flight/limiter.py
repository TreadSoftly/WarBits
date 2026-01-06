from __future__ import annotations

import math
from typing import Dict, Optional, Tuple

import numpy as np

from ..math3d import safe_unit
from .kinematics import slerp_dir
from .types import FlightLimits

Vec3 = np.ndarray


def limit_velocity_vector(
    v_current_mps: Vec3,
    v_desired_mps: Vec3,
    dt_s: float,
    limits: FlightLimits,
    *,
    eps: float = 1e-9,
) -> Tuple[Vec3, Dict[str, float]]:
    """Clamp a desired velocity vector to what the aircraft can physically do (cheaply).

    This is the “make scripted paths obey physics” helper.

    It enforces (when available):
    - max turn rate (from max bank + g limit; optionally overridden)
    - max speed and min speed (stall margin / safe minimum)
    - max climb / descent rate
    - max longitudinal acceleration (optional)

    Returns: (v_limited_mps, debug_dict)

    Notes:
    - This is intentionally a *kinematic limiter*, not an aerodynamic integrator.
    - It is deterministic and allocation-light for per-frame use.
    """
    dt = float(dt_s)
    if dt <= 0.0:
        raise ValueError(f"dt_s must be > 0, got {dt_s}")

    v_cur = np.asarray(v_current_mps, dtype=float)
    v_des = np.asarray(v_desired_mps, dtype=float)
    if v_cur.shape != (3,) or v_des.shape != (3,):
        raise ValueError("v_current_mps and v_desired_mps must be shape (3,).")

    speed_cur = float(np.linalg.norm(v_cur))
    speed_des = float(np.linalg.norm(v_des))

    # Pick directions (robust to near-zero speed)
    dir_cur = safe_unit(v_cur) if speed_cur > eps else safe_unit(v_des if speed_des > eps else np.array([1.0, 0.0, 0.0]))
    dir_des = safe_unit(v_des) if speed_des > eps else dir_cur

    debug: Dict[str, float] = {}
    debug["speed_cur"] = speed_cur
    debug["speed_des"] = speed_des

    # ---- Speed limiting (accel + min/max speed) ----
    speed_lim = speed_des

    if limits.max_accel_mps2 is not None:
        a = float(limits.max_accel_mps2)
        speed_low = max(0.0, speed_cur - a * dt)
        speed_high = speed_cur + a * dt
        speed_before = speed_lim
        speed_lim = float(min(max(speed_lim, speed_low), speed_high))
        debug["speed_accel_clamp_from"] = speed_before
        debug["speed_accel_clamp_to"] = speed_lim

    if limits.max_speed_mps is not None:
        speed_before = speed_lim
        speed_lim = float(min(speed_lim, float(limits.max_speed_mps)))
        debug["speed_max_clamp_from"] = speed_before
        debug["speed_max_clamp_to"] = speed_lim

    min_speed = float(max(0.0, limits.min_speed_mps))
    if speed_lim < min_speed:
        # If we have an accel cap, min speed might be unreachable this frame.
        if limits.max_accel_mps2 is not None and speed_cur < min_speed:
            a = float(limits.max_accel_mps2)
            max_reachable = speed_cur + a * dt
            if max_reachable < min_speed:
                debug["min_speed_unreachable"] = 1.0
                speed_lim = max_reachable
            else:
                speed_lim = min_speed
        else:
            speed_lim = min_speed
        debug["speed_min_clamp_to"] = speed_lim

    # ---- Turn rate limiting (direction change) ----
    # Use a speed reference to avoid absurd turn rates at tiny speeds.
    speed_ref = max(speed_cur, speed_lim, min_speed, 1.0)

    omega_lim = float(limits.turn_rate_limit_rad_s(speed_ref))
    max_angle = float(omega_lim * dt)

    # Keep max_angle sane; prevents weirdness if omega_lim is huge due to tiny speed.
    max_angle = min(max_angle, math.radians(60.0))  # hard sanity cap per tick
    debug["turn_rate_limit_rad_s"] = omega_lim
    debug["turn_max_angle_rad"] = max_angle

    # Compute the slerp factor
    # Angle computed via dot to avoid importing more helpers.
    dot = float(np.clip(np.dot(dir_cur, dir_des), -1.0, 1.0))
    angle = float(math.acos(dot))
    debug["turn_angle_requested_rad"] = angle

    if angle <= 1e-12 or max_angle <= 0.0:
        dir_lim = dir_des if angle <= max_angle else dir_cur
    else:
        if angle > max_angle:
            t = max_angle / angle
            dir_lim = slerp_dir(dir_cur, dir_des, t)
            debug["turn_clamped"] = 1.0
            debug["turn_slerp_t"] = t
        else:
            dir_lim = dir_des
            debug["turn_clamped"] = 0.0
            debug["turn_slerp_t"] = 1.0

    # ---- Climb/descent rate limiting (optional) ----
    v_lim = dir_lim * speed_lim
    vz = float(v_lim[2])

    if limits.max_climb_rate_mps is not None:
        max_climb = float(limits.max_climb_rate_mps)
        if vz > max_climb:
            v_lim = _clamp_vertical_rate(v_lim, speed_lim, max_vz=max_climb, min_vz=None)
            debug["climb_rate_clamped"] = 1.0

    if limits.max_descent_rate_mps is not None:
        max_desc = float(limits.max_descent_rate_mps)
        if vz < -max_desc:
            v_lim = _clamp_vertical_rate(v_lim, speed_lim, max_vz=None, min_vz=-max_desc)
            debug["descent_rate_clamped"] = 1.0

    debug["speed_out"] = float(np.linalg.norm(v_lim))
    return v_lim, debug


def _clamp_vertical_rate(v: Vec3, speed_target: float, *, max_vz: Optional[float], min_vz: Optional[float]) -> Vec3:
    """Adjust direction so that vertical component respects caps while keeping |v| ~= speed_target."""
    v = np.asarray(v, dtype=float)
    vx, vy, vz = float(v[0]), float(v[1]), float(v[2])

    if max_vz is not None:
        vz = min(vz, float(max_vz))
    if min_vz is not None:
        vz = max(vz, float(min_vz))

    speed_target = float(max(speed_target, 0.0))

    # Recompute horizontal speed required to keep magnitude constant.
    h2 = max(speed_target * speed_target - vz * vz, 0.0)
    h = math.sqrt(h2)

    h_cur = math.hypot(vx, vy)
    if h_cur <= 1e-12:
        # No defined horizontal direction; pick a deterministic axis.
        return np.array([h, 0.0, vz], dtype=float)

    scale = h / h_cur
    return np.array([vx * scale, vy * scale, vz], dtype=float)
