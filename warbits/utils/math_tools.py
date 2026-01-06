# ── warbits/utils/math_tools.py ──────────────────────────────────────────────
from __future__ import annotations

import math

import numpy as np
from numpy.typing import NDArray

from ..physics import ballistics as _ballistics  # ← fixed import

__all__ = [
    "clamp",
    "deg2rad",
    "rad2deg",
    "vec_norm",
    "unit_vector",
    "clamp_xyz_arrays",
]

# ── scalar helpers ───────────────────────────────────────────────────────────
def clamp(v: float, lo: float, hi: float) -> float:
    if lo > hi:
        raise ValueError(f"clamp() lower bound {lo} exceeds upper bound {hi}")
    try:
        return max(lo, min(hi, v))
    except TypeError as exc:  # pragma: no cover – misuse
        raise TypeError("clamp() expects three real numbers") from exc


def deg2rad(deg: float) -> float:  # convenience wrapper
    return math.radians(deg)


def rad2deg(rad: float) -> float:
    return math.degrees(rad)


# ── vector helpers ───────────────────────────────────────────────────────────
def vec_norm(x: float, y: float, z: float) -> float:
    return math.sqrt(x * x + y * y + z * z)


def unit_vector(x: float, y: float, z: float) -> tuple[float, float, float]:
    mag = vec_norm(x, y, z)
    if mag < 1e-9:
        return (0.0, 0.0, 1.0)
    return (x / mag, y / mag, z / mag)


# ── ndarray helpers ──────────────────────────────────────────────────────────
def clamp_xyz_arrays(
    x: NDArray[np.float64],
    y: NDArray[np.float64],
    z: NDArray[np.float64],
) -> tuple[NDArray[np.float64], NDArray[np.float64], NDArray[np.float64]]:
    return _ballistics.clamp_xyz_arrays(x, y, z)
