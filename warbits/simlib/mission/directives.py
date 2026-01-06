from __future__ import annotations

import dataclasses
from typing import Any, Dict, Optional, Tuple

import numpy as np


@dataclasses.dataclass(frozen=True)
class MissionDirective:
    kind: str
    payload: Dict[str, Any]


@dataclasses.dataclass(frozen=True)
class HUDMessageDirective(MissionDirective):
    text: str
    level: str = "info"  # info/warn/error
    ttl_s: float = 3.0

    def __init__(self, text: str, level: str = "info", ttl_s: float = 3.0):
        super().__init__(kind="hud_message", payload={"text": text, "level": level, "ttl_s": float(ttl_s)})
        object.__setattr__(self, "text", text)
        object.__setattr__(self, "level", level)
        object.__setattr__(self, "ttl_s", float(ttl_s))


@dataclasses.dataclass(frozen=True)
class SetFlagDirective(MissionDirective):
    flag: str
    value: Any

    def __init__(self, flag: str, value: Any):
        super().__init__(kind="set_flag", payload={"flag": flag, "value": value})
        object.__setattr__(self, "flag", flag)
        object.__setattr__(self, "value", value)


@dataclasses.dataclass(frozen=True)
class SpawnDirective(MissionDirective):
    """Request that the simulation spawns an entity.

    The simulation is the authority on entity creation. The mission layer only requests it.
    """

    entity_type: str
    entity_id: str
    team: str
    pos_m: np.ndarray
    vel_mps: np.ndarray
    tags: Tuple[str, ...] = ()

    def __init__(
        self,
        entity_type: str,
        entity_id: str,
        team: str,
        pos_m: np.ndarray,
        vel_mps: np.ndarray,
        tags: Tuple[str, ...] = (),
    ):
        payload = {
            "entity_type": entity_type,
            "entity_id": entity_id,
            "team": team,
            "pos_m": np.asarray(pos_m, dtype=np.float64).reshape(3).tolist(),
            "vel_mps": np.asarray(vel_mps, dtype=np.float64).reshape(3).tolist(),
            "tags": list(tags),
        }
        super().__init__(kind="spawn", payload=payload)
        object.__setattr__(self, "entity_type", entity_type)
        object.__setattr__(self, "entity_id", entity_id)
        object.__setattr__(self, "team", team)
        object.__setattr__(self, "pos_m", np.asarray(pos_m, dtype=np.float64).reshape(3))
        object.__setattr__(self, "vel_mps", np.asarray(vel_mps, dtype=np.float64).reshape(3))
        object.__setattr__(self, "tags", tuple(tags))


@dataclasses.dataclass(frozen=True)
class DespawnDirective(MissionDirective):
    entity_id: str

    def __init__(self, entity_id: str):
        super().__init__(kind="despawn", payload={"entity_id": entity_id})
        object.__setattr__(self, "entity_id", entity_id)
