from __future__ import annotations

import dataclasses
from typing import Dict, List, Sequence, TypeAlias, cast

import numpy as np
from numpy.typing import NDArray

from .directives import HUDMessageDirective, MissionDirective
from .types import WorldView

FloatArray: TypeAlias = NDArray[np.float64]


@dataclasses.dataclass
class Trigger:
    """Base trigger.

    Triggers are evaluated each mission tick.
    When they fire, they return directives and (usually) disable themselves unless repeatable.
    """

    id: str
    enabled: bool = True
    repeatable: bool = False
    has_fired: bool = False

    def check(self, world: WorldView, sim_events: Sequence[object], flags: Dict[str, object]) -> bool:
        return False

    def fire(self, world: WorldView, sim_events: Sequence[object], flags: Dict[str, object]) -> List[MissionDirective]:
        self.has_fired = True
        self.enabled = self.repeatable
        return []

    def tick(self, world: WorldView, sim_events: Sequence[object], flags: Dict[str, object]) -> List[MissionDirective]:
        if not self.enabled:
            return []
        if self.check(world, sim_events, flags):
            return self.fire(world, sim_events, flags)
        return []


@dataclasses.dataclass
class TimeTrigger(Trigger):
    fire_time_s: float = 0.0

    def check(self, world: WorldView, sim_events: Sequence[object], flags: Dict[str, object]) -> bool:
        return float(world.snapshot().time_s) >= float(self.fire_time_s)

    def fire(self, world: WorldView, sim_events: Sequence[object], flags: Dict[str, object]) -> List[MissionDirective]:
        super().fire(world, sim_events, flags)
        return [
            HUDMessageDirective(f"Trigger {self.id} fired at t={world.snapshot().time_s:.1f}s", level="info", ttl_s=3.0)
        ]


@dataclasses.dataclass
class FlagTrigger(Trigger):
    flag: str = ""
    equals: object = True

    def check(self, world: WorldView, sim_events: Sequence[object], flags: Dict[str, object]) -> bool:
        return flags.get(self.flag, None) == self.equals

    def fire(self, world: WorldView, sim_events: Sequence[object], flags: Dict[str, object]) -> List[MissionDirective]:
        super().fire(world, sim_events, flags)
        return [HUDMessageDirective(f"Flag trigger: {self.flag} == {self.equals}", level="info", ttl_s=4.0)]


@dataclasses.dataclass
class EventCountTrigger(Trigger):
    """Fires when the number of events of a given attribute reaches a threshold.

    Example: count impacts.
    """

    event_attr: str = "kind"  # attribute name or dict key
    event_value: object = "impact"
    threshold: int = 1

    def check(self, world: WorldView, sim_events: Sequence[object], flags: Dict[str, object]) -> bool:
        c = 0
        for ev in sim_events:
            v: object | None = None
            if hasattr(ev, self.event_attr):
                v = getattr(ev, self.event_attr)
            elif isinstance(ev, dict) and self.event_attr in ev:
                ev_map = cast(Dict[str, object], ev)
                v = ev_map.get(self.event_attr)
            if v == self.event_value:
                c += 1
            if c >= int(self.threshold):
                return True
        return False

    def fire(self, world: WorldView, sim_events: Sequence[object], flags: Dict[str, object]) -> List[MissionDirective]:
        super().fire(world, sim_events, flags)
        return [
            HUDMessageDirective(
                f"EventCountTrigger fired: {self.threshold}x {self.event_value}", level="info", ttl_s=4.0
            )
        ]


@dataclasses.dataclass
class EnterZoneTrigger(Trigger):
    entity_id: str = ""
    center_m: FloatArray = dataclasses.field(default_factory=lambda: np.zeros(3, dtype=np.float64))
    radius_m: float = 500.0

    def check(self, world: WorldView, sim_events: Sequence[object], flags: Dict[str, object]) -> bool:
        try:
            pose = world.get_pose(self.entity_id)
        except Exception:
            return False
        d = float(np.linalg.norm(pose.pos_m - np.asarray(self.center_m, dtype=np.float64).reshape(3)))
        return d <= float(self.radius_m)

    def fire(self, world: WorldView, sim_events: Sequence[object], flags: Dict[str, object]) -> List[MissionDirective]:
        super().fire(world, sim_events, flags)
        return [HUDMessageDirective(f"{self.entity_id} entered zone.", level="info", ttl_s=4.0)]
