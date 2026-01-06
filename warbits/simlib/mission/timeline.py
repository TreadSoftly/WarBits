from __future__ import annotations

import dataclasses
from typing import Callable, List, Optional, Sequence, Tuple

from .directives import MissionDirective
from .types import WorldView


@dataclasses.dataclass(frozen=True)
class TimelineItem:
    time_s: float
    directives: Tuple[MissionDirective, ...]


@dataclasses.dataclass
class Timeline:
    """A deterministic timeline of directives."""

    items: List[TimelineItem] = dataclasses.field(default_factory=list)
    _idx: int = 0

    def add(self, time_s: float, directives: Sequence[MissionDirective]) -> None:
        self.items.append(TimelineItem(time_s=float(time_s), directives=tuple(directives)))
        self.items.sort(key=lambda it: it.time_s)

    def reset(self) -> None:
        self._idx = 0

    def tick(self, world: WorldView) -> List[MissionDirective]:
        out: List[MissionDirective] = []
        now = float(world.snapshot().time_s)
        while self._idx < len(self.items) and now >= float(self.items[self._idx].time_s):
            out.extend(list(self.items[self._idx].directives))
            self._idx += 1
        return out
