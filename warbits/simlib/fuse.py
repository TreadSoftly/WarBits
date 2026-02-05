"""Fuse logic utilities.

This module centralizes "when does it detonate?" logic so rockets/bombs/warheads
all behave consistently and are data-driven.

It is deterministic and does not touch rendering.

Typical lifecycle:
- On spawn: FuseState(t_spawn, armed=False)
- Each tick: update() with current time, impact flag, proximity info
- When it returns True: detonate and mark state.detonated
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, TypeAlias

import numpy as np
from numpy.typing import NDArray

FloatArray: TypeAlias = NDArray[np.float64]


@dataclass(frozen=True)
class FuseSpec:
    fuse_type: str  # "impact" | "timed" | "proximity" | "impact_or_proximity"
    arming_time_s: float = 0.0
    impact_delay_s: float = 0.0
    time_to_detonate_s: Optional[float] = None  # for timed fuses
    proximity_radius_m: Optional[float] = None  # for proximity fuses

    def validate(self) -> None:
        if self.arming_time_s < 0:
            raise ValueError("arming_time_s must be >= 0")
        if self.impact_delay_s < 0:
            raise ValueError("impact_delay_s must be >= 0")
        if self.time_to_detonate_s is not None and self.time_to_detonate_s < 0:
            raise ValueError("time_to_detonate_s must be >= 0")
        if self.proximity_radius_m is not None and self.proximity_radius_m < 0:
            raise ValueError("proximity_radius_m must be >= 0")
        if self.fuse_type not in {"impact", "timed", "proximity", "impact_or_proximity"}:
            raise ValueError(f"Unknown fuse_type: {self.fuse_type}")


@dataclass
class FuseState:
    t_spawn_s: float
    armed: bool = False
    detonated: bool = False
    t_impact_s: Optional[float] = None

    def reset(self, t_spawn_s: float) -> None:
        self.t_spawn_s = float(t_spawn_s)
        self.armed = False
        self.detonated = False
        self.t_impact_s = None


def update_fuse(
    spec: FuseSpec,
    state: FuseState,
    *,
    time_s: float,
    projectile_pos: FloatArray,
    target_pos: Optional[FloatArray] = None,
    impact: bool = False,
) -> bool:
    """Update fuse state and return True if detonation should occur."""
    spec.validate()
    if state.detonated:
        return True

    t = float(time_s)
    since_spawn = t - float(state.t_spawn_s)

    if not state.armed and since_spawn >= float(spec.arming_time_s):
        state.armed = True

    # Timed fuse
    if spec.fuse_type == "timed" and spec.time_to_detonate_s is not None:
        if since_spawn >= float(spec.time_to_detonate_s):
            state.detonated = True
            return True

    # Impact fuse
    if impact and state.armed and spec.fuse_type in {"impact", "impact_or_proximity"}:
        if state.t_impact_s is None:
            state.t_impact_s = t
        if (t - float(state.t_impact_s)) >= float(spec.impact_delay_s):
            state.detonated = True
            return True

    # Proximity fuse
    if spec.fuse_type in {"proximity", "impact_or_proximity"} and state.armed:
        if spec.proximity_radius_m is None or target_pos is None:
            return False
        p = np.asarray(projectile_pos, dtype=float)
        tp = np.asarray(target_pos, dtype=float)
        d = float(np.linalg.norm(p - tp))
        if d <= float(spec.proximity_radius_m):
            state.detonated = True
            return True

    return False
