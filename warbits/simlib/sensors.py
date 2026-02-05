"""Sensor modeling helpers (simple, deterministic).

This module is intentionally "good enough" rather than pretending to be a full EW/EO model.

What you get:
- FOV + range gating
- optional line-of-sight gating (terrain LOS function)
- scan rate (sensors don't update every frame if you don't want them to)
- simple probability-of-detection curve + noise

What you do NOT get (yet):
- track filtering (Kalman etc.)
- clutter modeling
- ECM/ECCM
- detailed radar equation

Those can be layered on later without breaking the interface.

All distances are meters, angles are radians/degrees as named.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Sequence, TypeAlias, cast

import numpy as np
from numpy.typing import NDArray

from .math3d import angle_between, safe_unit
from .rng import DeterministicRNG
from .units import deg_to_rad

FloatArray: TypeAlias = NDArray[np.float64]
LOSFunc = Callable[[FloatArray, FloatArray], bool]


@dataclass(frozen=True)
class SensorSpec:
    sensor_id: str
    kind: str  # "radar" | "ir" | "optical" | "lidar" (extensible)
    fov_deg: float
    max_range_m: float
    min_range_m: float = 0.0
    scan_rate_hz: float = 5.0
    # Detection curve parameters (simple)
    p_detect_near: float = 0.98
    p_detect_far: float = 0.10  # at max_range
    noise_range_m: float = 0.0  # additive Gaussian noise
    noise_bearing_deg: float = 0.0
    require_los: bool = True

    def validate(self) -> None:
        if self.max_range_m <= 0:
            raise ValueError("max_range_m must be positive")
        if self.min_range_m < 0:
            raise ValueError("min_range_m must be >= 0")
        if self.fov_deg <= 0:
            raise ValueError("fov_deg must be positive")
        if self.scan_rate_hz <= 0:
            raise ValueError("scan_rate_hz must be positive")
        if not (0.0 <= self.p_detect_far <= 1.0 and 0.0 <= self.p_detect_near <= 1.0):
            raise ValueError("p_detect must be within [0,1]")


@dataclass
class SensorState:
    last_scan_t: float = -1e9
    # Track memory can live here later (track IDs, last seen, etc.)
    track_memory: Dict[str, float] = field(default_factory=lambda: cast(Dict[str, float], {}))


@dataclass(frozen=True)
class Detection:
    sensor_id: str
    target_id: str
    time_s: float
    range_m: float
    bearing_deg: float
    elevation_deg: float
    confidence: float  # 0..1


def _p_detect_linear(spec: SensorSpec, rng_m: float) -> float:
    # Linear interpolation: near->far
    if rng_m <= spec.min_range_m:
        return 0.0
    if rng_m >= spec.max_range_m:
        return spec.p_detect_far
    t = (rng_m - spec.min_range_m) / max(1e-9, (spec.max_range_m - spec.min_range_m))
    return (1.0 - t) * spec.p_detect_near + t * spec.p_detect_far


def scan(
    spec: SensorSpec,
    state: SensorState,
    *,
    own_id: str,
    own_pos: FloatArray,
    own_forward: FloatArray,
    targets: Sequence[tuple[str, FloatArray]],  # (target_id, target_pos)
    time_s: float,
    rng: Optional[DeterministicRNG] = None,
    los_fn: Optional[LOSFunc] = None,
    visibility: float = 1.0,  # 0..1 (weather can scale this)
) -> List[Detection]:
    """Perform a sensor scan and return detections."""
    spec.validate()
    if rng is None:
        rng = DeterministicRNG.from_seed(0).split(spec.sensor_id)

    dt_since = float(time_s) - float(state.last_scan_t)
    scan_period = 1.0 / float(spec.scan_rate_hz)
    if dt_since < scan_period:
        return []

    state.last_scan_t = float(time_s)

    own_pos = np.asarray(own_pos, dtype=float)
    fwd = safe_unit(np.asarray(own_forward, dtype=float), fallback=np.array([1.0, 0.0, 0.0], dtype=float))

    half_fov_rad = deg_to_rad(float(spec.fov_deg)) * 0.5

    dets: List[Detection] = []
    gen = rng.generator()

    for target_id, target_pos in targets:
        if target_id == own_id:
            continue
        tp = np.asarray(target_pos, dtype=float)
        rel = tp - own_pos
        rng_m = float(np.linalg.norm(rel))
        if rng_m < float(spec.min_range_m) or rng_m > float(spec.max_range_m):
            continue

        # FOV check
        ang = angle_between(fwd, rel)
        if ang > half_fov_rad:
            continue

        # LOS check
        if spec.require_los and los_fn is not None:
            if not bool(los_fn(own_pos, tp)):
                continue

        # Probability of detection
        p = _p_detect_linear(spec, rng_m) * float(max(0.0, min(1.0, visibility)))
        if gen.random() > p:
            continue

        # Compute noisy bearing/elevation in a simple local frame
        # Bearing: angle in XY plane from +X
        x, y, z = float(rel[0]), float(rel[1]), float(rel[2])
        bearing = math.degrees(math.atan2(y, x))
        horiz = math.hypot(x, y)
        elev = math.degrees(math.atan2(z, horiz))

        if spec.noise_range_m > 0:
            rng_m = float(rng_m + gen.normal(0.0, float(spec.noise_range_m)))
        if spec.noise_bearing_deg > 0:
            bearing = float(bearing + gen.normal(0.0, float(spec.noise_bearing_deg)))
            elev = float(elev + gen.normal(0.0, float(spec.noise_bearing_deg)))

        dets.append(
            Detection(
                sensor_id=spec.sensor_id,
                target_id=str(target_id),
                time_s=float(time_s),
                range_m=float(max(0.0, rng_m)),
                bearing_deg=float(bearing),
                elevation_deg=float(elev),
                confidence=float(p),
            )
        )

    return dets
