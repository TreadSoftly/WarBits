"""Projection helpers.

We keep this small and intentionally *not* tied to any renderer.

Renderers can:
- implement their own projector using their camera/projection APIs, OR
- use the pinhole projector here as a fast approximation.

The output is NDC coordinates in [-1,+1].
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np

from .types import NDC, CameraInfo, Vec3


class ScreenProjector:
    """Interface for world -> screen projection."""

    def project_ndc(self, world_pos_m: Vec3) -> Optional[NDC]:
        """Return (x_ndc, y_ndc) or None if behind camera."""
        raise NotImplementedError


@dataclass
class PinholeProjector(ScreenProjector):
    """Simple pinhole camera projection.

    This is not meant to perfectly match Matplotlib/Panda3D; it's for:
    - deterministic unit tests
    - headless HUD computations
    - fallback mode
    """

    camera: CameraInfo

    def project_ndc(self, world_pos_m: Vec3) -> Optional[NDC]:
        cam = self.camera
        fwd = _safe_unit(cam.forward)
        up = _safe_unit(cam.up)
        right = _safe_unit(np.cross(fwd, up))
        # Re-orthonormalize up (avoid drift)
        up = _safe_unit(np.cross(right, fwd))

        rel = world_pos_m - cam.position_m
        # Camera space: x=right, y=up, z=forward
        x = float(np.dot(rel, right))
        y = float(np.dot(rel, up))
        z = float(np.dot(rel, fwd))
        if z <= 1e-6:
            return None

        fov_y = np.deg2rad(cam.fov_y_deg)
        tan_y = np.tan(0.5 * fov_y)
        tan_x = tan_y * cam.aspect

        x_ndc = (x / z) / tan_x
        y_ndc = (y / z) / tan_y
        return (float(x_ndc), float(y_ndc))


def _safe_unit(v: Vec3) -> Vec3:
    n = float(np.linalg.norm(v))
    if n <= 1e-12:
        return np.array([1.0, 0.0, 0.0], dtype=float)
    return (v / n).astype(float)
