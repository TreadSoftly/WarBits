from __future__ import annotations

import dataclasses
from typing import Dict, List, Optional, Sequence

from .types import WorldView


@dataclasses.dataclass(frozen=True)
class ScoreEvent:
    time_s: float
    points: float
    reason: str


@dataclasses.dataclass
class ScoreModel:
    """Simple scoring model you can expand later.

    This lives in mission-land because scoring is *rules*, not physics.
    """

    score: float = 0.0
    history: List[ScoreEvent] = dataclasses.field(default_factory=list)

    def add(self, time_s: float, points: float, reason: str) -> None:
        self.score += float(points)
        self.history.append(ScoreEvent(time_s=float(time_s), points=float(points), reason=str(reason)))

    def on_sim_events(self, world: WorldView, sim_events: Sequence[object]) -> None:
        # Hook point: if your sim emits ImpactEvent/ExplosionEvent you can score them here.
        # We keep it generic in this library.
        return
