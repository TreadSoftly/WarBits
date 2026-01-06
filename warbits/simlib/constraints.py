"""Flight/vehicle constraint helpers.

This provides math utilities to enforce realistic envelopes without embedding
policy into the renderer or scenario scripts.

Typical uses:
- Limit turn rate based on g-limit and current speed
- Clamp commanded acceleration / velocity changes
- Keep AI from cheating (instant turns, instant speed changes)
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from .constants import G0_MPS2
from .math3d import clamp, clamp_vec_norm, safe_unit


def max_turn_rate_rad_s(speed_mps: float, *, g_limit: float = 9.0, min_speed_mps: float = 1.0) -> float:
    """Max instantaneous turn rate for level coordinated turn (approx).

    Using: ω = g0 * sqrt(n^2 - 1) / V
    where n is load factor ("g"), V is speed.

    If g_limit <= 1, turn rate is zero (can't bank without losing altitude in this model).
    """
    v = max(float(speed_mps), float(min_speed_mps))
    n = float(g_limit)
    if n <= 1.0:
        return 0.0
    return G0_MPS2 * math.sqrt(n * n - 1.0) / v


def clamp_turn_rate(desired_rate_rad_s: float, speed_mps: float, *, g_limit: float = 9.0) -> float:
    wmax = max_turn_rate_rad_s(speed_mps, g_limit=g_limit)
    return clamp(float(desired_rate_rad_s), -wmax, wmax)


def clamp_accel_vector(accel_mps2: np.ndarray, *, max_accel_mps2: float) -> np.ndarray:
    return clamp_vec_norm(np.asarray(accel_mps2, dtype=float), float(max_accel_mps2))


def rotate_towards(
    current_dir: np.ndarray,
    desired_dir: np.ndarray,
    *,
    max_turn_rate_rad_s: float,
    dt: float,
    eps: float = 1e-9,
) -> np.ndarray:
    """Rotate a direction vector towards another, limited by turn rate.

    This is a *direction-only* helper (no roll). It's useful for simplified AI steering,
    waypoint following, and "good enough" pursuit behavior.

    Args:
        current_dir: (3,) current unit-ish direction
        desired_dir: (3,) desired unit-ish direction
        max_turn_rate_rad_s: maximum angular change per second
        dt: time step

    Returns:
        new_dir: (3,) unit vector
    """
    c = safe_unit(current_dir, fallback=np.array([1.0, 0.0, 0.0], dtype=float), eps=eps)
    d = safe_unit(desired_dir, fallback=c, eps=eps)

    # Compute angle between
    dot_cd = float(np.dot(c, d))
    dot_cd = clamp(dot_cd, -1.0, 1.0)
    ang = math.acos(dot_cd)

    if ang < 1e-12:
        return d

    max_ang = float(max_turn_rate_rad_s) * float(dt)
    if max_ang <= 0.0:
        return c
    if ang <= max_ang:
        return d

    # Slerp on the unit sphere for direction vectors:
    # new = (sin((1-t)ang)/sin(ang)) * c + (sin(t ang)/sin(ang)) * d
    t = max_ang / ang
    sa = math.sin(ang)
    if abs(sa) < 1e-12:
        return d
    s1 = math.sin((1.0 - t) * ang) / sa
    s2 = math.sin(t * ang) / sa
    new_dir = s1 * c + s2 * d
    return safe_unit(new_dir, fallback=c, eps=eps)


@dataclass(frozen=True)
class Envelope:
    """Simple envelope constraints for a platform."""

    g_limit: float = 9.0
    max_accel_mps2: float = 50.0  # generic
    max_speed_mps: float | None = None
    min_speed_mps: float | None = None

    def clamp_speed(self, speed_mps: float) -> float:
        v = float(speed_mps)
        if self.max_speed_mps is not None:
            v = min(v, float(self.max_speed_mps))
        if self.min_speed_mps is not None:
            v = max(v, float(self.min_speed_mps))
        return v
