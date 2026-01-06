from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np


@dataclass
class ProjectileSegmentBatch:
    """Preallocated projectile line segments.

    Many renderers represent a projectile as a short line segment from the previous position
    to the current position (motion sells speed, and it avoids requiring actual bullet meshes).

    This object owns a single `(max_segments, 2, 3)` float32 array that is *reused* every frame.

    Upstream rule:
        Provide **compact** arrays of active projectiles (no boolean masking here). This keeps
        `update()` allocation-free.
    """

    max_segments: int

    def __post_init__(self) -> None:
        self._segments: np.ndarray = np.zeros((self.max_segments, 2, 3), dtype=np.float32)
        self.count: int = 0

    @property
    def buffer(self) -> np.ndarray:
        """The full preallocated segment buffer (do not slice-write beyond `count`)."""
        return self._segments

    def update(
        self,
        prev_pos_m: np.ndarray,
        curr_pos_m: np.ndarray,
        *,
        max_copy: Optional[int] = None,
    ) -> np.ndarray:
        """Update the batch segments.

        Args:
            prev_pos_m: `(N, 3)` array of previous projectile positions in meters.
            curr_pos_m: `(N, 3)` array of current projectile positions in meters.
            max_copy: optional cap for copying fewer than `max_segments` (useful for LOD).

        Returns:
            A view into the internal buffer with shape `(count, 2, 3)`.
        """

        if prev_pos_m.shape != curr_pos_m.shape:
            raise ValueError(
                f"prev_pos_m shape {prev_pos_m.shape} must match curr_pos_m shape {curr_pos_m.shape}"
            )
        if prev_pos_m.ndim != 2 or prev_pos_m.shape[1] != 3:
            raise ValueError("positions must be shaped (N, 3)")

        n = int(prev_pos_m.shape[0])
        cap = self.max_segments
        if max_copy is not None:
            cap = min(cap, int(max_copy))

        m = min(n, cap)
        if m <= 0:
            self.count = 0
            return self._segments[:0]

        # Copy with float32 coercion only if needed.
        # (astype(copy=False) returns a view when possible)
        p = np.asarray(prev_pos_m, dtype=np.float32)
        c = np.asarray(curr_pos_m, dtype=np.float32)

        self._segments[:m, 0, :] = p[:m]
        self._segments[:m, 1, :] = c[:m]
        self.count = m
        return self._segments[:m]

    def clear(self) -> None:
        self.count = 0
