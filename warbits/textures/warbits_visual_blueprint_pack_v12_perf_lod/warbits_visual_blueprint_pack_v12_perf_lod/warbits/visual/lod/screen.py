from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class CameraModel:
    """A tiny camera model for LOD decisions.

    We keep this intentionally minimal so it can be used without importing a renderer.

    - `vfov_deg`: vertical field of view (degrees)
    - `viewport_height_px`: viewport height in pixels

    If you only know horizontal FOV, convert:
        vfov = 2*atan(tan(hfov/2)/aspect)
    """

    vfov_deg: float
    viewport_height_px: int

    @property
    def vfov_rad(self) -> float:
        return math.radians(self.vfov_deg)


def projected_radius_px(radius_m: float, distance_m: float, cam: CameraModel) -> float:
    """Project a world-space radius to approximate screen pixels.

    This is an approximation, but it’s stable, deterministic, and plenty good enough
    for LOD tier selection.

    Returns:
        radius in **pixels**.
    """

    if radius_m <= 0.0:
        return 0.0
    if distance_m <= 1e-6:
        # Camera is basically inside the object.
        return float(cam.viewport_height_px)

    half_vfov = 0.5 * cam.vfov_rad
    denom = math.tan(half_vfov)
    if denom <= 1e-9:
        return float(cam.viewport_height_px)

    # normalized device coordinate scale:
    # radius_ndc ~ radius / (distance * tan(vfov/2))
    radius_ndc = radius_m / (distance_m * denom)

    # NDC [-1, 1] maps to viewport; half height is viewport_height_px/2.
    return radius_ndc * (0.5 * float(cam.viewport_height_px))
