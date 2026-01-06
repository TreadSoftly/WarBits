from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

import numpy as np


def make_unit_starburst_segments(rays: int = 12) -> np.ndarray:
    """Create unit-length starburst segments in the XY plane.

    Returns
    -------
    segments:
        (rays,2,3) float32 segments from origin to (cos(theta), sin(theta), 0).
    """
    rays = max(4, int(rays))
    ang = np.linspace(0.0, 2.0 * np.pi, rays, endpoint=False, dtype=np.float32)
    ends = np.stack([np.cos(ang), np.sin(ang), np.zeros_like(ang)], axis=1)
    seg = np.zeros((rays, 2, 3), dtype=np.float32)
    seg[:, 1] = ends
    return seg


@dataclass(frozen=True)
class BurstParams:
    max_bursts: int = 256
    rays: int = 12
    lifetime_frames: int = 18
    radius_m: float = 8.0


class BurstPool:
    """Simple expanding starburst/impact visual.

    This is intentionally cheap: no terrain-normal alignment here. If you want
    terrain-aligned splats, rotate the segments in the renderer using the
    surface normal.
    """

    def __init__(self, params: BurstParams):
        if params.max_bursts <= 0:
            raise ValueError("max_bursts must be > 0")
        self.params = params
        self._unit = make_unit_starburst_segments(params.rays)
        self._segs_per = self._unit.shape[0]

        self._centers = np.zeros((params.max_bursts, 3), dtype=np.float32)
        self._start = np.full((params.max_bursts,), -1, dtype=np.int32)
        self._alive = np.zeros((params.max_bursts,), dtype=np.bool_)
        self._radius = np.full((params.max_bursts,), params.radius_m, dtype=np.float32)
        self._life = np.full((params.max_bursts,), params.lifetime_frames, dtype=np.int32)

        self._cursor = 0

    def reset(self) -> None:
        self._start.fill(-1)
        self._alive.fill(False)
        self._cursor = 0

    def spawn(
        self,
        center_xyz_m: np.ndarray,
        *,
        frame_idx: int,
        radius_m: Optional[float] = None,
        lifetime_frames: Optional[int] = None,
    ) -> None:
        slot = int(self._cursor)
        self._cursor = (slot + 1) % self.params.max_bursts

        self._centers[slot] = center_xyz_m.astype(np.float32, copy=False)
        self._start[slot] = int(frame_idx)
        self._alive[slot] = True
        if radius_m is not None:
            self._radius[slot] = float(radius_m)
        if lifetime_frames is not None:
            self._life[slot] = int(lifetime_frames)

    def build_segments(self, *, frame_idx: int) -> Tuple[np.ndarray, np.ndarray]:
        alive = np.nonzero(self._alive)[0]
        if len(alive) == 0:
            return (
                np.zeros((0, 2, 3), dtype=np.float32),
                np.zeros((0,), dtype=np.float32),
            )

        unit = self._unit
        rays = self._segs_per
        total = len(alive) * rays
        segments = np.zeros((total, 2, 3), dtype=np.float32)
        alpha = np.zeros((total,), dtype=np.float32)

        out = 0
        for slot in alive:
            start = int(self._start[slot])
            age = int(frame_idx) - start
            life = int(self._life[slot])
            if age >= life:
                self._alive[slot] = False
                continue
            t = max(0.0, min(1.0, age / max(1, life - 1)))
            # Expand then fade.
            radius = float(self._radius[slot]) * (0.2 + 0.8 * t)
            a = 1.0 - t

            seg = unit * radius
            seg = seg + self._centers[slot]

            segments[out : out + rays] = seg
            alpha[out : out + rays] = a
            out += rays

        return segments[:out], alpha[:out]
