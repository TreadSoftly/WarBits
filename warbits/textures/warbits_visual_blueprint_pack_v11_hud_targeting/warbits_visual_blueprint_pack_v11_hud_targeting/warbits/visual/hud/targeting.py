"""Targeting / aiming math for HUD symbology.

This is not your physics engine. It's *pilot symbology*.
We aim for:
- deterministic
- stable
- cheap
- "good enough" lead for visual pippers

If you later want a perfect ballistic lead indicator, you can plug in
true solver outputs here.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np

from .types import Vec3


@dataclass(frozen=True)
class LeadSolution:
    intercept_time_s: float
    aim_direction_unit: Vec3
    aim_point_m: Vec3


def solve_intercept_no_gravity(
    shooter_pos_m: Vec3,
    target_pos_m: Vec3,
    target_vel_mps: Vec3,
    projectile_speed_mps: float,
    *,
    min_t_s: float = 0.0,
    max_t_s: float = 60.0,
) -> Optional[float]:
    """Closed-form lead time ignoring gravity.

    Solves |r + v t| = s t for t.

    Returns smallest positive t within [min_t_s, max_t_s], or None.
    """

    s = float(projectile_speed_mps)
    if s <= 1e-6:
        return None

    r = (target_pos_m - shooter_pos_m).astype(float)
    v = target_vel_mps.astype(float)

    a = float(np.dot(v, v) - s * s)
    b = float(2.0 * np.dot(r, v))
    c = float(np.dot(r, r))

    # Handle near-linear case
    if abs(a) < 1e-12:
        if abs(b) < 1e-12:
            return None
        t = -c / b
        if min_t_s <= t <= max_t_s:
            return float(t)
        return None

    disc = b * b - 4.0 * a * c
    if disc < 0.0:
        return None

    sqrt_disc = float(np.sqrt(disc))
    t1 = (-b - sqrt_disc) / (2.0 * a)
    t2 = (-b + sqrt_disc) / (2.0 * a)

    candidates = [t for t in (t1, t2) if min_t_s <= t <= max_t_s]
    if not candidates:
        return None

    # smallest positive
    candidates = [t for t in candidates if t > 1e-6]
    return float(min(candidates)) if candidates else None


def lead_solution_simple(
    shooter_pos_m: Vec3,
    shooter_vel_mps: Vec3,
    target_pos_m: Vec3,
    target_vel_mps: Vec3,
    projectile_speed_mps: float,
    *,
    gravity_mps2: float = 9.80665,
    gravity_axis: Vec3 = np.array([0.0, 0.0, -1.0], dtype=float),
    include_shooter_velocity: bool = True,
) -> Optional[LeadSolution]:
    """Compute an aim point and direction for a simple lead indicator.

    Model:
    - projectile has constant speed (muzzle_speed) relative to shooter
    - optionally add shooter velocity (simple approximation)
    - constant gravity acceleration (for "aim above" correction)

    This is intended for HUD pippers; it does *not* replace your physics.
    """

    s = float(projectile_speed_mps)
    if s <= 1e-6:
        return None

    # Relative target velocity wrt shooter
    rel_v = (target_vel_mps - (shooter_vel_mps if include_shooter_velocity else 0.0)).astype(float)

    t = solve_intercept_no_gravity(shooter_pos_m, target_pos_m, rel_v, s)
    if t is None:
        return None

    # Gravity correction: aim at where target will be, plus 0.5*g*t^2 upward (opposite gravity)
    g = float(gravity_mps2)
    g_dir = _safe_unit(gravity_axis)
    grav = -g * g_dir  # acceleration vector

    predicted_target = (target_pos_m + target_vel_mps * t).astype(float)
    aim_point = predicted_target - 0.5 * grav * (t * t)

    dir_vec = (aim_point - shooter_pos_m).astype(float)
    dir_unit = _safe_unit(dir_vec)

    return LeadSolution(intercept_time_s=float(t), aim_direction_unit=dir_unit, aim_point_m=aim_point)


def _safe_unit(v: Vec3) -> Vec3:
    n = float(np.linalg.norm(v))
    if n <= 1e-12:
        return np.array([1.0, 0.0, 0.0], dtype=float)
    return (v / n).astype(float)
