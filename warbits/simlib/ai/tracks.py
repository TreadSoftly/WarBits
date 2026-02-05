from __future__ import annotations

import dataclasses
from typing import Dict, List, Optional, TypeAlias, cast

import numpy as np
from numpy.typing import NDArray

from .filters import AlphaBetaFilter
from .rng import DeterministicRNG, stable_hash64

Vec3: TypeAlias = NDArray[np.float64]


@dataclasses.dataclass(frozen=True)
class Observation:
    """A generic observation in world coordinates (SI units)."""

    time_s: float
    sensor_id: str
    pos_m: Vec3  # shape (3,)
    # Optional quality/confidence: [0,1]
    quality: float = 1.0
    # Optional: who observed this (entity id), if relevant
    observer_id: str = ""


@dataclasses.dataclass
class Track:
    track_id: str
    filter: AlphaBetaFilter
    last_update_s: float
    confidence: float = 0.2
    sensor_ids: set[str] = dataclasses.field(default_factory=lambda: cast(set[str], set()))

    @property
    def pos_m(self) -> Vec3:
        return self.filter.x_m

    @property
    def vel_mps(self) -> Vec3:
        return self.filter.v_mps


@dataclasses.dataclass
class TrackManager:
    """Lightweight deterministic track manager.

    Association:
    - nearest-neighbor gating in position space
    - deterministic ordering for stability

    Intended usage:
    - feed this manager observations from your sensor model
    - AI consumes stable track IDs instead of raw detections

    This is not a full multi-hypothesis tracker (MHT). It's deliberately
    "good enough" for fast sims and deterministic AI.
    """

    rng: DeterministicRNG
    gate_m: float = 300.0
    max_age_s: float = 5.0
    alpha: float = 0.75
    beta: float = 0.08
    min_confidence: float = 0.05
    max_confidence: float = 1.0
    confidence_gain: float = 0.25
    confidence_decay_per_s: float = 0.15

    _tracks: Dict[str, Track] = dataclasses.field(default_factory=lambda: cast(Dict[str, Track], {}), init=False)

    def tracks(self) -> List[Track]:
        # stable ordering
        return [self._tracks[k] for k in sorted(self._tracks.keys())]

    def _new_track_id(self, obs: Observation, n: int) -> str:
        # stable id derived from RNG seed + observation time + counter
        h = stable_hash64(self.rng.seed_u64, obs.sensor_id, float(obs.time_s), n, obs.observer_id)
        return f"trk-{h:016x}"

    def _distance(self, a: Vec3, b: Vec3) -> float:
        d = np.asarray(a, dtype=np.float64).reshape(3) - np.asarray(b, dtype=np.float64).reshape(3)
        return float(np.linalg.norm(d))

    def prune(self, now_s: float) -> None:
        dead: List[str] = []
        for tid, trk in self._tracks.items():
            age = float(now_s) - float(trk.last_update_s)
            # confidence decay
            trk.confidence = max(self.min_confidence, trk.confidence - self.confidence_decay_per_s * max(0.0, age))
            if age > self.max_age_s or trk.confidence <= self.min_confidence + 1e-12:
                dead.append(tid)
        for tid in dead:
            del self._tracks[tid]

    def ingest(self, obs: Observation) -> str:
        now = float(obs.time_s)
        self.prune(now)

        pos = np.asarray(obs.pos_m, dtype=np.float64).reshape(3)

        # Find best match track within gate (deterministic tie-breaking: tid sort)
        best_tid: Optional[str] = None
        best_dist = float("inf")
        for tid in sorted(self._tracks.keys()):
            trk = self._tracks[tid]
            d = self._distance(trk.pos_m, pos)
            if d <= self.gate_m and d < best_dist:
                best_dist = d
                best_tid = tid

        if best_tid is None:
            # Create new track
            tid = self._new_track_id(obs, len(self._tracks))
            f = AlphaBetaFilter(alpha=self.alpha, beta=self.beta)
            f.update(pos, dt_s=1.0)  # initialize
            trk = Track(track_id=tid, filter=f, last_update_s=now, confidence=max(0.2, float(obs.quality)))
            trk.sensor_ids.add(obs.sensor_id)
            self._tracks[tid] = trk
            return tid

        # Update existing
        trk = self._tracks[best_tid]
        dt = max(1e-6, now - float(trk.last_update_s))
        trk.filter.update(pos, dt_s=dt)
        trk.last_update_s = now
        trk.sensor_ids.add(obs.sensor_id)
        # confidence update
        trk.confidence = min(self.max_confidence, trk.confidence + self.confidence_gain * float(obs.quality))
        return best_tid
