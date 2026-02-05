from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass(frozen=True)
class LODPolicy:
    """Selects a LOD name based on distance.

    This is intentionally simple and deterministic.
    The renderer can override or ignore if it has a better screen-space metric.

    Example:
      LODPolicy(thresholds_m=(300.0, 900.0), lod_names=("lod0","lod1","lod2"))
    """

    thresholds_m: Tuple[float, ...] = (350.0, 900.0, 1800.0)
    lod_names: Tuple[str, ...] = ("lod0", "lod1", "lod2", "lod3")

    def pick(self, distance_m: float) -> Optional[str]:
        """Return the chosen LOD name, or None to use base edges."""
        if distance_m < 0:
            distance_m = 0.0

        # If there are no lod names, caller will use base edges.
        if not self.lod_names:
            return None

        # distance < t0 => lod0
        # t0 <= distance < t1 => lod1
        # ...
        # distance >= last threshold => last lod name
        for i, t in enumerate(self.thresholds_m):
            if distance_m < t:
                return self.lod_names[min(i, len(self.lod_names) - 1)]
        return self.lod_names[min(len(self.thresholds_m), len(self.lod_names) - 1)]
