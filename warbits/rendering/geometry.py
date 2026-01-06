from __future__ import annotations

import math
from typing import Tuple

import numpy as np
from numpy.typing import NDArray

Vector3 = Tuple[float, float, float]

_UP_G = np.array([0.0, 0.0, 1.0], dtype=np.float32)
_RIGHT_G = np.array([1.0, 0.0, 0.0], dtype=np.float32)


def orientation_matrix(direction: Vector3) -> NDArray[np.float32]:
    dx, dy, dz = direction
    mag = float(np.sqrt(dx * dx + dy * dy + dz * dz))
    if mag < 1e-6:
        dx, dy, dz, mag = 1.0, 0.0, 0.0, 1.0
    fwd = np.array([dx / mag, dy / mag, dz / mag], dtype=np.float32)
    side = np.cross(fwd, _UP_G)
    side_mag = float(np.linalg.norm(side))
    if side_mag < 1e-6:
        side = np.cross(fwd, _RIGHT_G)
        side_mag = float(np.linalg.norm(side))
    if side_mag < 1e-6:
        side_mag = 1.0
    side /= side_mag
    up = np.cross(side, fwd)
    return np.stack([fwd, side, up], axis=1)


def transform_faces(
    base: NDArray[np.float32],
    position: Vector3,
    direction: Vector3,
    out: NDArray[np.float32],
) -> None:
    dx, dy, dz = direction
    mag = float(math.sqrt(dx * dx + dy * dy + dz * dz))
    if mag < 1e-6:
        dx, dy, dz, mag = 1.0, 0.0, 0.0, 1.0
    fx = dx / mag
    fy = dy / mag
    fz = dz / mag

    sx = fy
    sy = -fx
    sz = 0.0
    side_mag = float(math.sqrt(sx * sx + sy * sy + sz * sz))
    if side_mag < 1e-6:
        sx = 0.0
        sy = fz
        sz = -fy
        side_mag = float(math.sqrt(sx * sx + sy * sy + sz * sz))
    if side_mag < 1e-6:
        side_mag = 1.0
    sx /= side_mag
    sy /= side_mag
    sz /= side_mag

    ux = sy * fz - sz * fy
    uy = sz * fx - sx * fz
    uz = sx * fy - sy * fx

    px, py, pz = position
    flat_base = base.reshape(-1, 3)
    flat_out = out.reshape(-1, 3)
    flat_out[:, 0] = flat_base[:, 0] * fx + flat_base[:, 1] * sx + flat_base[:, 2] * ux + px
    flat_out[:, 1] = flat_base[:, 0] * fy + flat_base[:, 1] * sy + flat_base[:, 2] * uy + py
    flat_out[:, 2] = flat_base[:, 0] * fz + flat_base[:, 1] * sz + flat_base[:, 2] * uz + pz


__all__ = ["orientation_matrix", "transform_faces", "Vector3"]
