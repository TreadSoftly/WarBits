from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

import numpy as np
from numpy.typing import NDArray


def make_unit_sphere_segments(lat_steps: int = 6, lon_steps: int = 12) -> NDArray[np.float_]:
    """Precompute wireframe sphere segments on a unit sphere.

    Returns
    -------
    seg:
        (N,2,3) float32 segments.

    Notes
    -----
    This is a deliberately *cheap* sphere representation: it draws a small set of
    latitude and longitude circles. That gives a readable "wireframe bubble" that
    looks like a simulation replay, while staying extremely light on geometry.
    """
    lat_steps = max(3, int(lat_steps))
    lon_steps = max(6, int(lon_steps))

    segs: list[list[NDArray[np.float_]]] = []

    # Latitude circles excluding the poles.
    for i in range(1, lat_steps):
        phi = np.pi * i / lat_steps
        z = np.cos(phi)
        r = np.sin(phi)
        t = np.linspace(0.0, 2.0 * np.pi, lon_steps + 1, dtype=np.float32)
        x = r * np.cos(t)
        y = r * np.sin(t)
        pts = np.stack([x, y, np.full_like(x, z)], axis=1)
        for j in range(lon_steps):
            segs.append([pts[j], pts[j + 1]])

    # Longitude circles.
    for j in range(lon_steps):
        theta = 2.0 * np.pi * j / lon_steps
        t = np.linspace(0.0, np.pi, lat_steps * 2 + 1, dtype=np.float32)
        x = np.cos(theta) * np.sin(t)
        y = np.sin(theta) * np.sin(t)
        z = np.cos(t)
        pts = np.stack([x, y, z], axis=1)
        for k in range(len(t) - 1):
            segs.append([pts[k], pts[k + 1]])

    seg = np.asarray(segs, dtype=np.float32)
    return seg


@dataclass(frozen=True)
class ExplosionParams:
    max_explosions: int = 128
    lifetime_frames: int = 30
    max_radius_m: float = 60.0
    sphere_lat_steps: int = 6
    sphere_lon_steps: int = 12


class ExplosionPool:
    """Expanding wireframe-sphere explosions with pooling.

    The pool owns the state; the renderer owns how those lines look.

    Use cases
    ---------
    - Missile / bomb detonation
    - Ground target hits
    - "small pop" aircraft hit effect

    Determinism
    ----------
    Pure math from inputs; no internal RNG.
    """

    def __init__(self, params: ExplosionParams):
        if params.max_explosions <= 0:
            raise ValueError("max_explosions must be > 0")
        self.params = params
        self._unit = make_unit_sphere_segments(params.sphere_lat_steps, params.sphere_lon_steps)
        self._segs_per = int(self._unit.shape[0])

        self._centers = np.zeros((params.max_explosions, 3), dtype=np.float32)
        self._start = np.full((params.max_explosions,), -1, dtype=np.int32)
        self._alive = np.zeros((params.max_explosions,), dtype=np.bool_)
        self._radius = np.full((params.max_explosions,), params.max_radius_m, dtype=np.float32)
        self._life = np.full((params.max_explosions,), params.lifetime_frames, dtype=np.int32)

        self._cursor = 0

    def reset(self) -> None:
        self._start.fill(-1)
        self._alive.fill(False)
        self._cursor = 0

    def spawn(
        self,
        center_xyz_m: NDArray[np.float_],
        *,
        frame_idx: int,
        max_radius_m: Optional[float] = None,
        lifetime_frames: Optional[int] = None,
    ) -> None:
        """Spawn (or overwrite) an explosion in the pool."""
        slot = int(self._cursor)
        self._cursor = (slot + 1) % self.params.max_explosions

        self._centers[slot] = center_xyz_m.astype(np.float32, copy=False)
        self._start[slot] = int(frame_idx)
        self._alive[slot] = True
        if max_radius_m is not None:
            self._radius[slot] = float(max_radius_m)
        else:
            self._radius[slot] = float(self.params.max_radius_m)

        if lifetime_frames is not None:
            self._life[slot] = int(lifetime_frames)
        else:
            self._life[slot] = int(self.params.lifetime_frames)

    def build_segments(self, *, frame_idx: int) -> Tuple[NDArray[np.float_], NDArray[np.float_]]:
        """Build segments for all active explosions at this frame."""
        alive = np.nonzero(self._alive)[0]
        if len(alive) == 0:
            return (
                np.zeros((0, 2, 3), dtype=np.float32),
                np.zeros((0,), dtype=np.float32),
            )

        unit = self._unit
        per = self._segs_per

        # Upper bound; we slice down after culling expired.
        total = len(alive) * per
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
            # Expand quickly, then slow (keeps it punchy without being huge).
            radius = float(self._radius[slot]) * (0.25 + 0.75 * (t ** 0.6))
            # Fade toward the end.
            a = 1.0 - (t ** 1.6)

            seg = unit * radius
            seg = seg + self._centers[slot]

            segments[out : out + per] = seg
            alpha[out : out + per] = a
            out += per

        return segments[:out], alpha[:out]
