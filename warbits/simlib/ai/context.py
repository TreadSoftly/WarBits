from __future__ import annotations

import dataclasses
from typing import Any, Callable, Dict, Optional, Protocol

import numpy as np

from .blackboard import Blackboard
from .rng import DeterministicRNG


class WorldView(Protocol):
    """Minimal world interface used by SmartLib AI modules.

    Keep this tiny and adaptable: your simulation can implement this with a small adapter.
    """

    def time_s(self) -> float: ...
    def dt_s(self) -> float: ...

    # Entity queries (IDs are intentionally opaque strings)
    def get_pos_m(self, entity_id: str) -> np.ndarray: ...
    def get_vel_mps(self, entity_id: str) -> np.ndarray: ...
    def is_alive(self, entity_id: str) -> bool: ...
    def list_entities(self, team: Optional[str] = None) -> list[str]: ...


@dataclasses.dataclass
class AIContext:
    """Standard context object passed through AI decision layers."""

    rng: DeterministicRNG
    bb: Blackboard
    world: Optional[WorldView] = None
    now_s: float = 0.0
    dt_s: float = 0.0

    # Optional scratchpad for per-tick computed values (avoid recomputation).
    cache: Dict[str, Any] = dataclasses.field(default_factory=dict)

    def fork(self, *key_parts: Any) -> "AIContext":
        """Create a deterministic sub-context with an RNG fork."""
        return AIContext(
            rng=self.rng.fork(*key_parts),
            bb=self.bb,
            world=self.world,
            now_s=self.now_s,
            dt_s=self.dt_s,
            cache=self.cache,
        )
