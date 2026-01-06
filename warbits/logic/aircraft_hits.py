from __future__ import annotations

import os
from typing import Tuple

import numpy as np
import numpy.typing as npt

from ..core.events import ImpactEvent
from ..logic.state import RUNTIME, ProjectileBuffer
from ..physics.explosions import spawn_explosion

__all__ = ["check_aircraft_hits"]

_F32Arr = npt.NDArray[np.float32]

_AIRCRAFT_HIT_RADIUS_ROCKET = 240.0
_AIRCRAFT_HIT_RADIUS_BOMB = 320.0
_AIRCRAFT_HIT_RADIUS_ROCKET_SQ = _AIRCRAFT_HIT_RADIUS_ROCKET * _AIRCRAFT_HIT_RADIUS_ROCKET
_AIRCRAFT_HIT_RADIUS_BOMB_SQ = _AIRCRAFT_HIT_RADIUS_BOMB * _AIRCRAFT_HIT_RADIUS_BOMB
_AIRCRAFT_EXPLOSION_SCALE_ROCKET = 0.55
_AIRCRAFT_EXPLOSION_SCALE_BOMB = 0.85
_AIRCRAFT_HIT_MIN_SAMPLE_ROCKET = 2
_AIRCRAFT_HIT_MIN_SAMPLE_BOMB = 6
def _bomb_hits_enabled() -> bool:
    return os.environ.get("WARBITS_AIRCRAFT_BOMB_HITS", "").lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def _segment_hits(
    paths: _F32Arr,
    sample_index: npt.NDArray[np.int32],
    target: Tuple[float, float, float],
    radius_sq: float,
    min_sample: int,
) -> npt.NDArray[np.bool_]:
    if paths.size == 0:
        return np.zeros(0, dtype=bool)
    n = int(paths.shape[0])
    if n == 0 or paths.shape[2] == 0:
        return np.zeros(n, dtype=bool)
    idx = np.clip(sample_index.astype(np.int64), 0, paths.shape[2] - 1)
    idx0 = np.maximum(idx - 1, 0)
    idx_expand = np.broadcast_to(idx[:, None, None], (n, 3, 1))
    idx0_expand = np.broadcast_to(idx0[:, None, None], (n, 3, 1))
    p1 = np.take_along_axis(paths, idx_expand, axis=2)[:, :, 0]
    p0 = np.take_along_axis(paths, idx0_expand, axis=2)[:, :, 0]
    v = p1 - p0
    w = np.array(target, dtype=np.float32) - p0
    v_len_sq = np.sum(v * v, axis=1)
    dot = np.sum(w * v, axis=1)
    t = np.zeros_like(dot, dtype=np.float32)
    np.divide(dot, v_len_sq, out=t, where=v_len_sq > 1e-9)
    t = np.clip(t, 0.0, 1.0)
    closest = p0 + v * t[:, None]
    dx = closest[:, 0] - target[0]
    dy = closest[:, 1] - target[1]
    dz = closest[:, 2] - target[2]
    hits = (dx * dx + dy * dy + dz * dz) <= radius_sq
    if sample_index.size:
        hits = hits & (sample_index >= min_sample)
    return hits


def _record_impact(
    frame: int,
    pos: Tuple[float, float, float],
    *,
    weapon: str,
) -> None:
    x, y, z = pos
    RUNTIME.impacts.append(
        ImpactEvent(
            frame=int(frame),
            x=float(x),
            y=float(y),
            z=float(z),
            target="aircraft",
            weapon=weapon,
        )
    )
    if os.environ.get("WARBITS_IMPACT_DEBUG", "").lower() in {"1", "true", "yes", "on"}:
        print(f"[impact] frame={frame} target=aircraft weapon={weapon} pos=({x:.1f},{y:.1f},{z:.1f})")


def _apply_hits(
    buffer: ProjectileBuffer,
    frame: int,
    pos: Tuple[float, float, float],
    *,
    weapon: str,
    radius_sq: float,
    explosion_scale: float,
    min_sample: int,
) -> None:
    paths = buffer.paths
    if paths.size == 0:
        return
    hits = _segment_hits(paths, buffer.sample_index, pos, radius_sq, min_sample)
    if hits.size == 0 or not bool(np.any(hits)):
        return
    rows = buffer.sample_positions()[3]
    if rows.size != hits.size:
        return
    buffer.remove(rows[hits])
    spawn_explosion(pos, scale=explosion_scale)
    _record_impact(frame, pos, weapon=weapon)


def check_aircraft_hits(frame: int, pos: Tuple[float, float, float]) -> None:
    """Detect rocket/bomb impacts against the player aircraft."""
    _apply_hits(
        RUNTIME.active_rockets,
        frame,
        pos,
        weapon="rocket",
        radius_sq=_AIRCRAFT_HIT_RADIUS_ROCKET_SQ,
        explosion_scale=_AIRCRAFT_EXPLOSION_SCALE_ROCKET,
        min_sample=_AIRCRAFT_HIT_MIN_SAMPLE_ROCKET,
    )
    if _bomb_hits_enabled():
        _apply_hits(
            RUNTIME.active_bombs,
            frame,
            pos,
            weapon="bomb",
            radius_sq=_AIRCRAFT_HIT_RADIUS_BOMB_SQ,
            explosion_scale=_AIRCRAFT_EXPLOSION_SCALE_BOMB,
            min_sample=_AIRCRAFT_HIT_MIN_SAMPLE_BOMB,
        )
