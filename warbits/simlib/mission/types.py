from __future__ import annotations

import dataclasses
from typing import Any, Dict, List, Optional, Protocol, Sequence, Tuple

import numpy as np


Team = str


@dataclasses.dataclass(frozen=True)
class Pose:
    pos_m: np.ndarray  # (3,)
    vel_mps: np.ndarray  # (3,)

    @staticmethod
    def from_arrays(pos_m: Sequence[float], vel_mps: Sequence[float]) -> "Pose":
        return Pose(
            pos_m=np.asarray(pos_m, dtype=np.float64).reshape(3),
            vel_mps=np.asarray(vel_mps, dtype=np.float64).reshape(3),
        )


@dataclasses.dataclass(frozen=True)
class EntitySnapshot:
    entity_id: str
    team: Team
    alive: bool
    pose: Pose
    tags: Tuple[str, ...] = ()

    def has_tag(self, tag: str) -> bool:
        return tag in self.tags


@dataclasses.dataclass(frozen=True)
class WorldSnapshot:
    time_s: float
    entities: Tuple[EntitySnapshot, ...]

    def get(self, entity_id: str) -> Optional[EntitySnapshot]:
        for e in self.entities:
            if e.entity_id == entity_id:
                return e
        return None

    def list_entities(self, team: Optional[Team] = None, alive_only: bool = True) -> List[str]:
        out: List[str] = []
        for e in self.entities:
            if team is not None and e.team != team:
                continue
            if alive_only and not e.alive:
                continue
            out.append(e.entity_id)
        return out


class WorldView(Protocol):
    """Protocol for mission logic. Your sim can provide an adapter."""

    def snapshot(self) -> WorldSnapshot: ...
    def is_alive(self, entity_id: str) -> bool: ...
    def get_pose(self, entity_id: str) -> Pose: ...
