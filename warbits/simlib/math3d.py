"""Fast, reusable 3D math utilities.

This is meant to replace copy/paste geometry code scattered across modules.

Conventions:
- Vectors are numpy arrays with shape (3,) or (N, 3).
- Quaternions are (w, x, y, z) and are expected to be unit length for rotations.
- All angles are radians unless explicitly named *_deg.

Numerical safety:
- Many functions accept an eps. If norms are < eps, we avoid division by zero
  and return a sensible fallback.
"""

from __future__ import annotations

import math

import numpy as np
import numpy.typing as npt

from .constants import EPS_NORM


ArrayF = npt.NDArray[np.float64]
Vec3 = ArrayF
Quat = ArrayF
Mat3 = ArrayF


def clamp(x: float, lo: float, hi: float) -> float:
    return lo if x < lo else hi if x > hi else x


def norm(v: Vec3) -> float:
    return float(np.linalg.norm(v))


def norm2(v: Vec3) -> float:
    return float(np.dot(v, v))


def unit(v: Vec3, *, eps: float = EPS_NORM) -> Vec3:
    """Return normalized vector; returns zeros if norm is too small."""
    n = np.linalg.norm(v)
    if float(n) < eps:
        return np.zeros(3, dtype=float)
    return v / n


def safe_unit(v: Vec3, *, fallback: Vec3 | None = None, eps: float = EPS_NORM) -> Vec3:
    """Normalize v, or return a normalized fallback if v is near-zero."""
    n = np.linalg.norm(v)
    if float(n) < eps:
        if fallback is None:
            return np.zeros(3, dtype=float)
        return unit(np.asarray(fallback, dtype=float), eps=eps)
    return v / n


def clamp_vec_norm(v: Vec3, max_norm: float, *, eps: float = EPS_NORM) -> Vec3:
    """Clamp vector magnitude to max_norm, preserving direction."""
    n = np.linalg.norm(v)
    n_f = float(n)
    if n_f < eps:
        return np.zeros(3, dtype=float)
    if n_f <= max_norm:
        return v
    return v * (max_norm / n_f)


def angle_between(a: Vec3, b: Vec3, *, eps: float = EPS_NORM) -> float:
    """Return angle between vectors in radians."""
    na = np.linalg.norm(a)
    nb = np.linalg.norm(b)
    na_f = float(na)
    nb_f = float(nb)
    if na_f < eps or nb_f < eps:
        return 0.0
    c = float(np.dot(a, b) / (na_f * nb_f))
    c = clamp(c, -1.0, 1.0)
    return float(math.acos(c))


def wrap_angle_rad(theta: float) -> float:
    """Wrap angle to [-pi, pi)."""
    # Using fmod keeps this deterministic and fast.
    twopi = 2.0 * math.pi
    t = math.fmod(theta + math.pi, twopi)
    if t < 0:
        t += twopi
    return t - math.pi


def wrap_angle_deg(theta_deg: float) -> float:
    return wrap_angle_rad(theta_deg * math.pi / 180.0) * 180.0 / math.pi


# ----------------------------
# Quaternion math
# ----------------------------

def quat_normalize(q: Quat, *, eps: float = EPS_NORM) -> Quat:
    n = float(np.linalg.norm(q))
    if n < eps:
        # Identity quaternion
        return np.array([1.0, 0.0, 0.0, 0.0], dtype=float)
    return q / n


def quat_conj(q: Quat) -> Quat:
    return np.array([q[0], -q[1], -q[2], -q[3]], dtype=float)


def quat_mul(a: Quat, b: Quat) -> Quat:
    """Hamilton product (a * b)."""
    aw, ax, ay, az = float(a[0]), float(a[1]), float(a[2]), float(a[3])
    bw, bx, by, bz = float(b[0]), float(b[1]), float(b[2]), float(b[3])
    return np.array(
        [
            aw * bw - ax * bx - ay * by - az * bz,
            aw * bx + ax * bw + ay * bz - az * by,
            aw * by - ax * bz + ay * bw + az * bx,
            aw * bz + ax * by - ay * bx + az * bw,
        ],
        dtype=float,
    )


def quat_from_axis_angle(axis: Vec3, angle_rad: float, *, eps: float = EPS_NORM) -> Quat:
    axis_u = safe_unit(axis, eps=eps)
    half = 0.5 * angle_rad
    s = math.sin(half)
    return quat_normalize(np.array([math.cos(half), axis_u[0] * s, axis_u[1] * s, axis_u[2] * s], dtype=float), eps=eps)


def quat_rotate_vec(q: Quat, v: Vec3) -> Vec3:
    """Rotate vector v by quaternion q."""
    qn = quat_normalize(q)
    vq = np.array([0.0, float(v[0]), float(v[1]), float(v[2])], dtype=float)
    rq = quat_mul(quat_mul(qn, vq), quat_conj(qn))
    return np.array([rq[1], rq[2], rq[3]], dtype=float)


def quat_from_two_vectors(a: Vec3, b: Vec3, *, eps: float = EPS_NORM) -> Quat:
    """Quaternion rotating vector a -> b (both can be non-unit)."""
    au = safe_unit(a, eps=eps)
    bu = safe_unit(b, eps=eps)
    dot_ab = float(np.dot(au, bu))
    # If vectors are nearly opposite, choose an arbitrary orthogonal axis
    if dot_ab < -1.0 + 1e-6:
        # Find orthogonal axis
        ortho = np.array([1.0, 0.0, 0.0], dtype=float)
        if abs(float(au[0])) > 0.9:
            ortho = np.array([0.0, 1.0, 0.0], dtype=float)
        axis = safe_unit(np.cross(au, ortho), eps=eps)
        return quat_from_axis_angle(axis, math.pi, eps=eps)
    axis = np.cross(au, bu)
    q = np.array([1.0 + dot_ab, float(axis[0]), float(axis[1]), float(axis[2])], dtype=float)
    return quat_normalize(q, eps=eps)


def rotation_matrix_from_forward_up(forward: Vec3, up: Vec3 = np.array([0.0, 0.0, 1.0], dtype=float), *, eps: float = EPS_NORM) -> Mat3:
    """Build a right-handed rotation matrix from forward and up.

    Returns matrix whose columns are [right, up_corrected, forward].
    """
    f = safe_unit(forward, fallback=np.array([1.0, 0.0, 0.0], dtype=float), eps=eps)
    r = np.cross(f, up)
    r = safe_unit(r, fallback=np.array([0.0, 1.0, 0.0], dtype=float), eps=eps)
    u = np.cross(r, f)
    u = safe_unit(u, fallback=np.array([0.0, 0.0, 1.0], dtype=float), eps=eps)
    # Columns: right, up, forward
    return np.stack([r, u, f], axis=1)


# ----------------------------
# Segment distance utilities
# ----------------------------

def closest_point_on_segment(p: Vec3, a: Vec3, b: Vec3, *, eps: float = EPS_NORM) -> Vec3:
    """Closest point to p on segment a->b."""
    ab = b - a
    ab2 = float(np.dot(ab, ab))
    if ab2 < eps * eps:
        return np.array(a, dtype=float)
    t = float(np.dot(p - a, ab) / ab2)
    t = clamp(t, 0.0, 1.0)
    return a + t * ab


def distance_point_segment(p: Vec3, a: Vec3, b: Vec3, *, eps: float = EPS_NORM) -> float:
    c = closest_point_on_segment(p, a, b, eps=eps)
    return float(np.linalg.norm(p - c))


def distance_point_segment_sq(p: Vec3, a: Vec3, b: Vec3, *, eps: float = EPS_NORM) -> float:
    c = closest_point_on_segment(p, a, b, eps=eps)
    d = p - c
    return float(np.dot(d, d))


def distance_point_segment_batch(p: Vec3, a: ArrayF, b: ArrayF, *, eps: float = EPS_NORM) -> ArrayF:
    """Vectorized point-to-segment distance for many segments.

    Args:
        p: (3,) point
        a: (N,3) segment starts
        b: (N,3) segment ends

    Returns:
        (N,) distances
    """
    p = np.asarray(p, dtype=float).reshape(1, 3)
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    ab = b - a
    ab2 = np.sum(ab * ab, axis=1)  # (N,)
    # Handle degenerate segments
    denom = np.where(ab2 < (eps * eps), 1.0, ab2)
    t = np.sum((p - a) * ab, axis=1) / denom
    t = np.clip(t, 0.0, 1.0)
    c = a + (ab * t[:, None])
    d = (p - c).reshape(-1, 3)
    return np.linalg.norm(d, axis=1)
