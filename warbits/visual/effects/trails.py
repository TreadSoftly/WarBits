from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional, Tuple

import numpy as np


@dataclass(frozen=True)
class TrailParams:
    """Configuration for a trail family.

    A trail family is a set of points tracked per object id across frames,
    then emitted as connected line segments with fading alpha.

    Typical families:
    - "tracers": bullets (short history, fast fade)
    - "contrails": aircraft trails (longer history, slower fade)
    - "smoke": rocket exhaust trails (medium history, slow drift)
    """

    max_objects: int = 2048
    history_len: int = 6
    min_segment_len_m: float = 0.25


class TrailRingBuffer:
    """Ring-buffer trails keyed by integer object ids.

    Design: fixed-size *slot table* with open addressing so we don't create
    or delete Python dict entries in the hot loop.

    For very high projectile counts, you can use a special mode:
    - If your ids are already in [0, max_objects) you can call `ingest_direct`.

    Output geometry is built with `build_segments()`.
    """

    def __init__(self, params: TrailParams):
        if params.max_objects <= 0:
            raise ValueError("max_objects must be > 0")
        if params.history_len < 2:
            raise ValueError("history_len must be >= 2")
        self.params = params
        # Slot table size: power of 2 for fast modulo.
        size = 1
        while size < params.max_objects * 2:
            size *= 2
        self._size = size
        self._keys = np.full((size,), -1, dtype=np.int64)
        self._used = np.zeros((size,), dtype=np.bool_)
        self._slot = np.full((size,), -1, dtype=np.int32)
        self._next_slot = 0

        # Per slot history
        self._hist = np.full((params.max_objects, params.history_len, 3), np.nan, dtype=np.float32)
        self._write = np.zeros((params.max_objects,), dtype=np.int32)
        self._alive = np.zeros((params.max_objects,), dtype=np.bool_)

    def reset(self) -> None:
        self._keys.fill(-1)
        self._used.fill(False)
        self._slot.fill(-1)
        self._next_slot = 0
        self._hist.fill(np.nan)
        self._write.fill(0)
        self._alive.fill(False)

    def _find(self, key: int) -> int:
        mask = self._size - 1
        i = (key * 11400714819323198485) & 0xFFFFFFFFFFFFFFFF  # 64-bit fibonacci hash
        idx = int(i & mask)
        step = 1
        while True:
            if not self._used[idx]:
                return idx
            if int(self._keys[idx]) == key:
                return idx
            idx = (idx + step) & mask
            step += 1

    def _ensure_slot(self, key: int) -> int:
        idx = self._find(int(key))
        if not self._used[idx]:
            if self._next_slot >= self.params.max_objects:
                # Hard cap reached: we drop this object id.
                return -1
            slot = int(self._next_slot)
            self._next_slot += 1
            self._used[idx] = True
            self._keys[idx] = int(key)
            self._slot[idx] = slot
            self._alive[slot] = True
            self._write[slot] = 0
            # Clear history for the new slot
            self._hist[slot].fill(np.nan)
            return slot
        return int(self._slot[idx])

    def ingest(self, ids: np.ndarray, positions_xyz: np.ndarray) -> None:
        """Ingest positions for arbitrary integer ids.

        Parameters
        ----------
        ids:
            (N,) int array-like.
        positions_xyz:
            (N,3) float array in meters.
        """
        if ids.ndim != 1:
            raise ValueError("ids must be 1D")
        if positions_xyz.ndim != 2 or positions_xyz.shape[1] != 3:
            raise ValueError("positions_xyz must be (N,3)")
        if len(ids) != len(positions_xyz):
            raise ValueError("ids and positions length mismatch")

        for i in range(len(ids)):
            slot = self._ensure_slot(int(ids[i]))
            if slot < 0:
                continue
            w = int(self._write[slot])
            self._hist[slot, w] = positions_xyz[i].astype(np.float32, copy=False)
            self._write[slot] = (w + 1) % self.params.history_len

    def ingest_direct(self, slots: np.ndarray, positions_xyz: np.ndarray) -> None:
        """Fast path: directly write positions into known slot indices.

        This assumes:
        - slots are in [0, max_objects)
        - slot i corresponds to a persistent object (projectile index)

        It's ideal when your simulation already stores projectiles in a dense buffer.
        """
        if slots.ndim != 1:
            raise ValueError("slots must be 1D")
        if positions_xyz.ndim != 2 or positions_xyz.shape[1] != 3:
            raise ValueError("positions_xyz must be (N,3)")
        if len(slots) != len(positions_xyz):
            raise ValueError("slots and positions length mismatch")

        for i in range(len(slots)):
            slot = int(slots[i])
            if slot < 0 or slot >= self.params.max_objects:
                continue
            if not self._alive[slot]:
                self._alive[slot] = True
                self._hist[slot].fill(np.nan)
                self._write[slot] = 0
            w = int(self._write[slot])
            self._hist[slot, w] = positions_xyz[i].astype(np.float32, copy=False)
            self._write[slot] = (w + 1) % self.params.history_len

    def build_segments(self) -> Tuple[np.ndarray, np.ndarray]:
        """Build line segments and alpha per segment.

        Returns
        -------
        segments:
            (M,2,3) float32 segments.
        alpha:
            (M,) float32 alpha weights in [0..1].
        """
        alive_slots = np.nonzero(self._alive)[0]
        if len(alive_slots) == 0:
            return (
                np.zeros((0, 2, 3), dtype=np.float32),
                np.zeros((0,), dtype=np.float32),
            )

        hist_len = self.params.history_len
        segs_per = hist_len - 1
        # Worst-case segment count (we'll filter later)
        total = len(alive_slots) * segs_per
        segments = np.zeros((total, 2, 3), dtype=np.float32)
        alpha = np.zeros((total,), dtype=np.float32)

        # Alpha gradient: newest segment highest alpha.
        # segment age 0 -> newest (alpha 1.0)
        # age segs_per-1 -> oldest (alpha ~0.1)
        age_alpha = np.linspace(1.0, 0.1, segs_per, dtype=np.float32)

        out = 0
        for slot in alive_slots:
            w = int(self._write[slot])
            # Reconstruct history in time order (oldest -> newest)
            idxs = (np.arange(hist_len, dtype=np.int32) + w) % hist_len
            pts = self._hist[slot, idxs]
            # Skip if no data
            if np.all(np.isnan(pts)):
                continue
            # Build consecutive segments
            for j in range(segs_per):
                a = pts[j]
                b = pts[j + 1]
                if np.any(np.isnan(a)) or np.any(np.isnan(b)):
                    continue
                if self.params.min_segment_len_m > 0:
                    if float(np.linalg.norm(b - a)) < self.params.min_segment_len_m:
                        continue
                segments[out, 0] = a
                segments[out, 1] = b
                # Newest segment is at j=segs_per-1 in this (oldest->newest) ordering
                alpha[out] = age_alpha[segs_per - 1 - j]
                out += 1

        return segments[:out], alpha[:out]
