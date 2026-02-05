from __future__ import annotations

import dataclasses
import enum
from typing import List, Optional, Sequence, Tuple, TypeAlias

import numpy as np
from numpy.typing import NDArray

from .directives import HUDMessageDirective, MissionDirective
from .types import WorldView

FloatArray: TypeAlias = NDArray[np.float64]


class ObjectiveStatus(enum.Enum):
    INACTIVE = 0
    ACTIVE = 1
    SUCCESS = 2
    FAILURE = 3


@dataclasses.dataclass
class Objective:
    """Base objective."""

    id: str
    title: str
    status: ObjectiveStatus = ObjectiveStatus.INACTIVE

    def activate(self) -> List[MissionDirective]:
        self.status = ObjectiveStatus.ACTIVE
        return []

    def update(self, world: WorldView, sim_events: Sequence[object]) -> List[MissionDirective]:
        # override
        return []

    def is_done(self) -> bool:
        return self.status in (ObjectiveStatus.SUCCESS, ObjectiveStatus.FAILURE)


@dataclasses.dataclass
class DestroyEntitiesObjective(Objective):
    targets: Tuple[str, ...] = ()
    success_message: str = "Targets destroyed."
    fail_if_any_missing: bool = False

    def activate(self) -> List[MissionDirective]:
        super().activate()
        return [HUDMessageDirective(f"Objective: {self.title}", level="info", ttl_s=4.0)]

    def update(self, world: WorldView, sim_events: Sequence[object]) -> List[MissionDirective]:
        if self.status is not ObjectiveStatus.ACTIVE:
            return []
        directives: List[MissionDirective] = []
        for tid in self.targets:
            try:
                alive = bool(world.is_alive(tid))
            except Exception:
                alive = False
                if self.fail_if_any_missing:
                    self.status = ObjectiveStatus.FAILURE
                    directives.append(HUDMessageDirective(f"Objective failed: missing {tid}", level="error", ttl_s=6.0))
                    return directives
            if alive:
                return directives  # still active
        self.status = ObjectiveStatus.SUCCESS
        directives.append(HUDMessageDirective(self.success_message, level="info", ttl_s=6.0))
        return directives


@dataclasses.dataclass
class SurviveObjective(Objective):
    entity_id: str = ""
    time_limit_s: Optional[float] = None
    start_time_s: Optional[float] = None
    success_message: str = "Survived."
    failure_message: str = "Destroyed."

    def activate(self) -> List[MissionDirective]:
        super().activate()
        self.start_time_s = None
        return [HUDMessageDirective(f"Objective: {self.title}", level="info", ttl_s=4.0)]

    def update(self, world: WorldView, sim_events: Sequence[object]) -> List[MissionDirective]:
        if self.status is not ObjectiveStatus.ACTIVE:
            return []
        directives: List[MissionDirective] = []
        snap = world.snapshot()
        if self.start_time_s is None:
            self.start_time_s = float(snap.time_s)

        if not world.is_alive(self.entity_id):
            self.status = ObjectiveStatus.FAILURE
            directives.append(HUDMessageDirective(self.failure_message, level="error", ttl_s=6.0))
            return directives

        if self.time_limit_s is not None:
            if (float(snap.time_s) - float(self.start_time_s)) >= float(self.time_limit_s):
                self.status = ObjectiveStatus.SUCCESS
                directives.append(HUDMessageDirective(self.success_message, level="info", ttl_s=6.0))
        return directives


@dataclasses.dataclass
class ReachZoneObjective(Objective):
    entity_id: str = ""
    center_m: FloatArray = dataclasses.field(default_factory=lambda: np.zeros(3, dtype=np.float64))
    radius_m: float = 500.0
    success_message: str = "Zone reached."
    failure_time_limit_s: Optional[float] = None
    start_time_s: Optional[float] = None

    def activate(self) -> List[MissionDirective]:
        super().activate()
        self.start_time_s = None
        return [HUDMessageDirective(f"Objective: {self.title}", level="info", ttl_s=4.0)]

    def update(self, world: WorldView, sim_events: Sequence[object]) -> List[MissionDirective]:
        if self.status is not ObjectiveStatus.ACTIVE:
            return []
        directives: List[MissionDirective] = []
        snap = world.snapshot()
        if self.start_time_s is None:
            self.start_time_s = float(snap.time_s)

        if not world.is_alive(self.entity_id):
            self.status = ObjectiveStatus.FAILURE
            directives.append(
                HUDMessageDirective(f"Objective failed: {self.entity_id} destroyed", level="error", ttl_s=6.0)
            )
            return directives

        pose = world.get_pose(self.entity_id)
        d = float(np.linalg.norm(pose.pos_m - np.asarray(self.center_m, dtype=np.float64).reshape(3)))
        if d <= float(self.radius_m):
            self.status = ObjectiveStatus.SUCCESS
            directives.append(HUDMessageDirective(self.success_message, level="info", ttl_s=6.0))
            return directives

        if self.failure_time_limit_s is not None:
            if (float(snap.time_s) - float(self.start_time_s)) >= float(self.failure_time_limit_s):
                self.status = ObjectiveStatus.FAILURE
                directives.append(
                    HUDMessageDirective("Objective failed: time limit exceeded", level="error", ttl_s=6.0)
                )
                return directives

        return directives


@dataclasses.dataclass
class TimeLimitObjective(Objective):
    time_limit_s: float = 10.0
    start_time_s: Optional[float] = None
    success_message: str = "Time elapsed."

    def activate(self) -> List[MissionDirective]:
        super().activate()
        self.start_time_s = None
        return [HUDMessageDirective(f"Objective: {self.title}", level="info", ttl_s=4.0)]

    def update(self, world: WorldView, sim_events: Sequence[object]) -> List[MissionDirective]:
        if self.status is not ObjectiveStatus.ACTIVE:
            return []
        directives: List[MissionDirective] = []
        now = float(world.snapshot().time_s)
        if self.start_time_s is None:
            self.start_time_s = now
        if (now - float(self.start_time_s)) >= float(self.time_limit_s):
            self.status = ObjectiveStatus.SUCCESS
            directives.append(HUDMessageDirective(self.success_message, level="info", ttl_s=6.0))
        return directives


@dataclasses.dataclass
class CompositeObjective(Objective):
    """Combine objectives with AND / OR logic."""

    mode: str = "and"  # "and" or "or"
    children: Tuple[Objective, ...] = ()

    def activate(self) -> List[MissionDirective]:
        super().activate()
        directives: List[MissionDirective] = [HUDMessageDirective(f"Objective: {self.title}", level="info", ttl_s=4.0)]
        for c in self.children:
            directives.extend(c.activate())
        return directives

    def update(self, world: WorldView, sim_events: Sequence[object]) -> List[MissionDirective]:
        if self.status is not ObjectiveStatus.ACTIVE:
            return []
        directives: List[MissionDirective] = []
        for c in self.children:
            directives.extend(c.update(world, sim_events))

        if not self.children:
            self.status = ObjectiveStatus.SUCCESS
            return directives

        m = self.mode.lower()
        if m == "and":
            if all(c.status is ObjectiveStatus.SUCCESS for c in self.children):
                self.status = ObjectiveStatus.SUCCESS
                directives.append(HUDMessageDirective("Objectives complete.", level="info", ttl_s=6.0))
            elif any(c.status is ObjectiveStatus.FAILURE for c in self.children):
                self.status = ObjectiveStatus.FAILURE
                directives.append(HUDMessageDirective("Objective set failed.", level="error", ttl_s=6.0))
        elif m == "or":
            if any(c.status is ObjectiveStatus.SUCCESS for c in self.children):
                self.status = ObjectiveStatus.SUCCESS
                directives.append(HUDMessageDirective("Objective complete.", level="info", ttl_s=6.0))
            elif all(c.status is ObjectiveStatus.FAILURE for c in self.children):
                self.status = ObjectiveStatus.FAILURE
                directives.append(HUDMessageDirective("All options failed.", level="error", ttl_s=6.0))
        else:
            raise ValueError(f"Unknown composite mode: {self.mode!r}")
        return directives
