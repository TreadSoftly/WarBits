"""Guidance / steering helpers.

These are meant for:
- enemy bogie pursuit that's constrained (no instant turns)
- future guided missiles (proportional navigation)
- waypoint following / autopilot behavior

All functions are deterministic and pure (no hidden state).

Important: These are *math tools*, not full autopilot logic.
A real autopilot also needs throttle control, energy management, and envelope
protection. This module gives you the pieces.
"""

from __future__ import annotations

from typing import TypeAlias

import numpy as np
from numpy.typing import NDArray

from .constants import EPS_NORM
from .math3d import clamp_vec_norm, safe_unit

FloatArray: TypeAlias = NDArray[np.float64]


def pure_pursuit_direction(own_pos: FloatArray, target_pos: FloatArray, *, eps: float = EPS_NORM) -> FloatArray:
    """Return unit vector from own -> target."""
    return safe_unit(np.asarray(target_pos, dtype=float) - np.asarray(own_pos, dtype=float), eps=eps)


def proportional_navigation_accel(
    own_pos: FloatArray,
    own_vel: FloatArray,
    target_pos: FloatArray,
    target_vel: FloatArray,
    *,
    nav_constant: float = 3.0,
    max_accel_mps2: float | None = None,
    eps: float = EPS_NORM,
) -> FloatArray:
    """3D proportional navigation acceleration command.

    Basic PN:
      a_cmd = N * Vc * (omega x u)
    where:
      r = target_pos - own_pos
      v = target_vel - own_vel  (relative velocity)
      u = r / |r|              (LOS unit)
      omega = (r x v) / |r|^2  (LOS angular rate vector)
      Vc = -dot(v, u)          (closing speed, positive when closing)

    Returns:
      acceleration vector in m/s^2 to be applied to the pursuer (missile/rocket/AI).
    """
    r = np.asarray(target_pos, dtype=float) - np.asarray(own_pos, dtype=float)
    v = np.asarray(target_vel, dtype=float) - np.asarray(own_vel, dtype=float)

    r2 = float(np.dot(r, r))
    if r2 < eps * eps:
        return np.zeros(3, dtype=float)

    r_norm = float(np.sqrt(r2))
    u = r / r_norm
    omega = np.cross(r, v) / r2  # rad/s vector (approx)
    vc = -float(np.dot(v, u))

    a = float(nav_constant) * vc * np.cross(omega, u)
    if max_accel_mps2 is not None:
        a = clamp_vec_norm(a, float(max_accel_mps2))
    return np.asarray(a, dtype=float)


def lead_pursuit_direction(
    own_pos: FloatArray,
    own_speed_mps: float,
    target_pos: FloatArray,
    target_vel: FloatArray,
    *,
    eps: float = EPS_NORM,
    max_time_s: float = 30.0,
) -> FloatArray:
    """Return a pursuit direction that leads the target.

    This solves a simple intercept approximation assuming:
    - pursuer travels at constant speed own_speed_mps
    - target has constant velocity target_vel

    If the quadratic has no good solution, falls back to pure pursuit.

    Returns:
        unit direction vector from own_pos.
    """
    p = np.asarray(own_pos, dtype=float)
    tp = np.asarray(target_pos, dtype=float)
    tv = np.asarray(target_vel, dtype=float)

    r = tp - p
    v = tv

    s = float(own_speed_mps)
    if s < eps:
        return safe_unit(r, eps=eps)

    # Solve |r + v t|^2 = (s t)^2
    # => (v·v - s^2) t^2 + 2 (r·v) t + (r·r) = 0
    a = float(np.dot(v, v) - s * s)
    b = 2.0 * float(np.dot(r, v))
    c = float(np.dot(r, r))

    t = None
    if abs(a) < 1e-12:
        # Linear
        if abs(b) > 1e-12:
            t_lin = -c / b
            if 0.0 < t_lin <= max_time_s:
                t = t_lin
    else:
        disc = b * b - 4.0 * a * c
        if disc >= 0.0:
            sqrt_disc = float(np.sqrt(disc))
            t1 = (-b - sqrt_disc) / (2.0 * a)
            t2 = (-b + sqrt_disc) / (2.0 * a)
            # Choose smallest positive
            candidates = [tt for tt in (t1, t2) if 0.0 < tt <= max_time_s]
            if candidates:
                t = min(candidates)

    if t is None:
        return safe_unit(r, eps=eps)

    aim_point = tp + tv * float(t)
    return safe_unit(aim_point - p, eps=eps)
    return safe_unit(aim_point - p, eps=eps)
