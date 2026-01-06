from __future__ import annotations

import math
from dataclasses import dataclass
from enum import IntEnum
from typing import Optional, Tuple


class LODLevel(IntEnum):
    """Discrete LOD tiers (HIGH < MED < LOW < ICON)."""

    HIGH = 0
    MED = 1
    LOW = 2
    ICON = 3


@dataclass(frozen=True)
class CameraModel:
    """Minimal camera model for LOD decisions."""

    vfov_deg: float
    viewport_height_px: int

    @property
    def vfov_rad(self) -> float:
        return math.radians(self.vfov_deg)


def projected_radius_px(radius_m: float, distance_m: float, cam: CameraModel) -> float:
    """Approximate screen-space radius in pixels."""
    if radius_m <= 0.0:
        return 0.0
    if distance_m <= 1e-6:
        return float(cam.viewport_height_px)
    half_vfov = 0.5 * cam.vfov_rad
    denom = math.tan(half_vfov)
    if denom <= 1e-9:
        return float(cam.viewport_height_px)
    radius_ndc = radius_m / (distance_m * denom)
    return radius_ndc * (0.5 * float(cam.viewport_height_px))


@dataclass(frozen=True)
class LODPolicy:
    """Hybrid LOD policy with distance + screen-size support."""

    # Distance-based thresholds (legacy)
    thresholds_m: Tuple[float, ...] = (350.0, 900.0, 1800.0)
    lod_names: Tuple[str, ...] = ("lod0", "lod1", "lod2", "lod3")

    # Screen-size thresholds
    px_high: float = 80.0
    px_med: float = 25.0
    px_low: float = 8.0

    # Distance clamps for screen-size policy
    max_high_distance_m: float = 3000.0
    max_med_distance_m: float = 10000.0
    max_low_distance_m: float = 25000.0

    @classmethod
    def defaults(cls) -> "LODPolicy":
        return cls()

    def pick(self, distance_m: float) -> Optional[str]:
        """Return a LOD name based on distance only (legacy behavior)."""
        if distance_m < 0:
            distance_m = 0.0
        if not self.lod_names:
            return None
        for i, t in enumerate(self.thresholds_m):
            if distance_m < t:
                return self.lod_names[min(i, len(self.lod_names) - 1)]
        return self.lod_names[min(len(self.thresholds_m), len(self.lod_names) - 1)]

    def select(self, distance_m: float, projected_px: float) -> LODLevel:
        """Return the LOD tier based on screen size + distance clamps."""
        if distance_m >= self.max_low_distance_m:
            return LODLevel.ICON
        if projected_px >= self.px_high and distance_m <= self.max_high_distance_m:
            return LODLevel.HIGH
        if projected_px >= self.px_med and distance_m <= self.max_med_distance_m:
            return LODLevel.MED
        if projected_px >= self.px_low:
            return LODLevel.LOW
        return LODLevel.ICON

    def select_lod(
        self,
        *,
        distance_m: Optional[float] = None,
        projected_px: Optional[float] = None,
    ) -> Optional[str]:
        """Return a LOD name; uses screen-size if provided, else distance-only."""
        dist = float(distance_m or 0.0)
        if projected_px is None:
            return self.pick(dist)
        level = self.select(dist, float(projected_px))
        return self._lod_name_for_level(level)

    def _lod_name_for_level(self, level: LODLevel) -> Optional[str]:
        order = (LODLevel.HIGH, LODLevel.MED, LODLevel.LOW, LODLevel.ICON)
        try:
            idx = order.index(level)
        except ValueError:
            return None
        if idx < len(self.lod_names):
            return self.lod_names[idx]
        return None


__all__ = [
    "LODLevel",
    "CameraModel",
    "projected_radius_px",
    "LODPolicy",
]
