from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

from .levels import LODLevel


@dataclass(frozen=True)
class LODPolicy:
    """Deterministic LOD selection policy.

    Supports both:
    - distance-only thresholds (legacy)
    - screen-size thresholds with distance clamps (preferred)
    """

    # Distance thresholds (legacy)
    thresholds_m: Tuple[float, ...] = (350.0, 900.0, 1800.0)
    lod_names: Tuple[str, ...] = ("lod0", "lod1", "lod2", "lod3")

    # Pixel-size gates
    px_high: float = 80.0
    px_med: float = 25.0
    px_low: float = 8.0

    # Distance clamps (meters)
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
        """Return the LOD tier for a single object."""
        if distance_m >= self.max_low_distance_m:
            return LODLevel.ICON

        # Pixel thresholds dominate, but distance clamps keep things sane.
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
        """Return a LOD name, using screen-size if provided."""
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
