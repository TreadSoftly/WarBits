from __future__ import annotations

from dataclasses import dataclass

from .levels import LODLevel


@dataclass(frozen=True)
class LODPolicy:
    """Deterministic LOD selection policy.

    The policy uses two signals:

    1) `distance_m` — how far the object is from the camera
    2) `projected_px` — how big its bounding radius is on screen (approx)

    Using projected size makes LOD decisions much more stable than using distance alone.

    Notes on thresholds:

    - Pixel thresholds are the primary selector.
    - Maximum-distance thresholds prevent a giant distant object from forcing HIGH LOD.

    This policy is pure-Python and deterministic; it has no renderer dependencies.
    """

    # Pixel-size gates
    px_high: float = 80.0
    px_med: float = 25.0
    px_low: float = 8.0

    # Distance clamps (meters)
    max_high_distance_m: float = 3000.0
    max_med_distance_m: float = 10000.0
    max_low_distance_m: float = 25000.0

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
