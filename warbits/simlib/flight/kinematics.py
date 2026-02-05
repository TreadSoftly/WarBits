from __future__ import annotations

import math
from typing import Tuple, TypeAlias

import numpy as np
from numpy.typing import NDArray

from ..math3d import angle_between, safe_unit

Vec3: TypeAlias = NDArray[np.float64]


def slerp_dir(u: Vec3, v: Vec3, t: float) -> Vec3:
    """Spherical linear interpolation between two direction vectors.

    Inputs do not need to be perfectly normalized; we normalize safely.

    Edge cases handled:
    - near-zero vectors: falls back to v
    - near-parallel: linear interpolate + renormalize
    - near-opposite: picks an arbitrary orthogonal axis deterministically

    Returns a unit vector.
    """
    t = float(t)
    if t <= 0.0:
        return safe_unit(u)
    if t >= 1.0:
        return safe_unit(v)

    u_hat = safe_unit(u)
    v_hat = safe_unit(v)

    dot = float(np.clip(np.dot(u_hat, v_hat), -1.0, 1.0))
    if dot > 0.9995:
        w = (1.0 - t) * u_hat + t * v_hat
        return safe_unit(w)

    if dot < -0.9995:
        # u and v are almost opposite; choose an orthogonal axis deterministically.
        abs_u = np.abs(u_hat)
        if abs_u[0] <= abs_u[1] and abs_u[0] <= abs_u[2]:
            ortho = np.array([1.0, 0.0, 0.0])
        elif abs_u[1] <= abs_u[2]:
            ortho = np.array([0.0, 1.0, 0.0])
        else:
            ortho = np.array([0.0, 0.0, 1.0])

        axis = safe_unit(np.cross(u_hat, ortho))
        angle = math.pi * t
        return rotate_about_axis(u_hat, axis, angle)

    theta = math.acos(dot)
    sin_theta = math.sin(theta)
    a = math.sin((1.0 - t) * theta) / sin_theta
    b = math.sin(t * theta) / sin_theta
    return safe_unit(a * u_hat + b * v_hat)


def rotate_about_axis(v: Vec3, axis: Vec3, angle_rad: float) -> Vec3:
    """Rotate vector v about a unit axis by angle (Rodrigues' rotation formula)."""
    v = np.asarray(v, dtype=float)
    k = safe_unit(axis)
    a = float(angle_rad)
    c = math.cos(a)
    s = math.sin(a)
    return (v * c) + (np.cross(k, v) * s) + (k * np.dot(k, v) * (1.0 - c))


def yaw_pitch_from_direction(dir_vec: Vec3) -> Tuple[float, float]:
    """Return (yaw, pitch) in radians from a direction vector.

    Convention:
    - +X forward, +Y right, +Z up
    - yaw is rotation about +Z (0 = +X, +pi/2 = +Y)
    - pitch is positive when pointing upward

    This is meant for HUD/debug and simple control logic.
    """
    d = safe_unit(dir_vec)
    yaw = math.atan2(float(d[1]), float(d[0]))
    horiz = math.hypot(float(d[0]), float(d[1]))
    pitch = math.atan2(float(d[2]), horiz)
    return yaw, pitch


def direction_from_yaw_pitch(yaw_rad: float, pitch_rad: float) -> Vec3:
    """Unit direction vector from yaw/pitch (radians)."""
    cy = math.cos(float(yaw_rad))
    sy = math.sin(float(yaw_rad))
    cp = math.cos(float(pitch_rad))
    sp = math.sin(float(pitch_rad))
    return safe_unit(np.array([cp * cy, cp * sy, sp], dtype=float))


def signed_angle_2d(a: Vec3, b: Vec3) -> float:
    """Signed angle from vector a to b in 2D (radians), in range [-pi, +pi]."""
    a_hat = safe_unit(np.array([a[0], a[1], 0.0], dtype=float))
    b_hat = safe_unit(np.array([b[0], b[1], 0.0], dtype=float))
    ang = angle_between(a_hat, b_hat)
    z = float(np.cross(a_hat, b_hat)[2])
    return float(ang if z >= 0.0 else -ang)
