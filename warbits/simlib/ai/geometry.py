from __future__ import annotations

import dataclasses
import math
from typing import Optional, Tuple

import numpy as np


def norm(v: np.ndarray) -> float:
    return float(np.linalg.norm(v))


def unit(v: np.ndarray, eps: float = 1e-12) -> np.ndarray:
    v = np.asarray(v, dtype=np.float64).reshape(3)
    n = norm(v)
    if n < eps:
        return np.array([1.0, 0.0, 0.0], dtype=np.float64)
    return v / n


def clamp(x: float, lo: float, hi: float) -> float:
    return float(max(lo, min(hi, x)))


def compute_lead_time(
    shooter_pos_m: np.ndarray,
    target_pos_m: np.ndarray,
    target_vel_mps: np.ndarray,
    projectile_speed_mps: float,
    max_time_s: float = 30.0,
) -> Optional[float]:
    """Solve for lead time t where |r + v*t| = s*t.

    r = target_pos - shooter_pos
    v = target_vel
    s = projectile_speed

    Returns:
    - t >= 0 if solvable, else None.
    """
    r = np.asarray(target_pos_m, dtype=np.float64).reshape(3) - np.asarray(shooter_pos_m, dtype=np.float64).reshape(3)
    v = np.asarray(target_vel_mps, dtype=np.float64).reshape(3)
    s = float(projectile_speed_mps)

    if s <= 1e-9:
        return None

    a = float(np.dot(v, v) - s * s)
    b = float(2.0 * np.dot(r, v))
    c = float(np.dot(r, r))

    if abs(a) < 1e-12:
        # linear: b*t + c = 0
        if abs(b) < 1e-12:
            return None
        t = -c / b
        if t < 0.0:
            return None
        return float(min(t, max_time_s))

    disc = b * b - 4.0 * a * c
    if disc < 0.0:
        return None
    sqrt_disc = math.sqrt(disc)
    t1 = (-b - sqrt_disc) / (2.0 * a)
    t2 = (-b + sqrt_disc) / (2.0 * a)

    ts = [t for t in (t1, t2) if t >= 0.0]
    if not ts:
        return None
    t = min(ts)
    if t > max_time_s:
        return None
    return float(t)


def compute_lead_point(
    shooter_pos_m: np.ndarray,
    target_pos_m: np.ndarray,
    target_vel_mps: np.ndarray,
    projectile_speed_mps: float,
    max_time_s: float = 30.0,
) -> Optional[np.ndarray]:
    t = compute_lead_time(shooter_pos_m, target_pos_m, target_vel_mps, projectile_speed_mps, max_time_s=max_time_s)
    if t is None:
        return None
    return np.asarray(target_pos_m, dtype=np.float64).reshape(3) + np.asarray(target_vel_mps, dtype=np.float64).reshape(3) * float(t)


def angle_between_rad(a: np.ndarray, b: np.ndarray, eps: float = 1e-12) -> float:
    ua = unit(a, eps=eps)
    ub = unit(b, eps=eps)
    d = clamp(float(np.dot(ua, ub)), -1.0, 1.0)
    return float(math.acos(d))


@dataclasses.dataclass(frozen=True)
class GunSolution:
    aim_dir_unit: np.ndarray  # unit vector
    time_to_impact_s: float
    lead_point_m: np.ndarray
    angle_off_boresight_rad: float


def compute_gun_solution(
    shooter_pos_m: np.ndarray,
    shooter_forward_unit: np.ndarray,
    target_pos_m: np.ndarray,
    target_vel_mps: np.ndarray,
    muzzle_speed_mps: float,
    max_time_s: float = 10.0,
) -> Optional[GunSolution]:
    lead = compute_lead_point(shooter_pos_m, target_pos_m, target_vel_mps, muzzle_speed_mps, max_time_s=max_time_s)
    if lead is None:
        return None
    aim_vec = lead - np.asarray(shooter_pos_m, dtype=np.float64).reshape(3)
    t = compute_lead_time(shooter_pos_m, target_pos_m, target_vel_mps, muzzle_speed_mps, max_time_s=max_time_s)
    if t is None:
        return None
    aim_unit = unit(aim_vec)
    off = angle_between_rad(shooter_forward_unit, aim_unit)
    return GunSolution(
        aim_dir_unit=aim_unit,
        time_to_impact_s=float(t),
        lead_point_m=lead,
        angle_off_boresight_rad=float(off),
    )
