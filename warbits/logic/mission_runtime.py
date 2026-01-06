from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Iterable, Sequence

from ..logic.state import RuntimeState
from ..simlib.mission.directives import HUDMessageDirective, MissionDirective
from ..simlib.mission.director import MissionDirector, MissionTickResult
from ..simlib.mission.objectives import Objective, ObjectiveStatus, TimeLimitObjective
from ..simlib.mission.types import EntitySnapshot, Pose, WorldSnapshot, WorldView


EntityProvider = Callable[[], Sequence[EntitySnapshot]]
TimeProvider = Callable[[], float]

DEFAULT_TIME_LIMIT_S = 1.0


def _new_entity_index() -> dict[str, EntitySnapshot]:
    return {}


def _new_directives() -> list[MissionDirective]:
    return []


@dataclass
class MissionWorldAdapter(WorldView):
    time_s: TimeProvider
    entity_provider: EntityProvider
    _snapshot: WorldSnapshot | None = None
    _index: dict[str, EntitySnapshot] = field(default_factory=_new_entity_index, init=False)

    def refresh(self) -> None:
        entities = tuple(self.entity_provider())
        self._snapshot = WorldSnapshot(time_s=float(self.time_s()), entities=entities)
        self._index = {ent.entity_id: ent for ent in entities}

    def snapshot(self) -> WorldSnapshot:
        if self._snapshot is None:
            self.refresh()
        assert self._snapshot is not None
        return self._snapshot

    def is_alive(self, entity_id: str) -> bool:
        ent = self._index.get(entity_id)
        return bool(ent.alive) if ent is not None else False

    def get_pose(self, entity_id: str) -> Pose:
        ent = self._index.get(entity_id)
        if ent is None:
            raise KeyError(entity_id)
        return ent.pose


@dataclass
class DestroyWithinTimeObjective(Objective):
    targets: tuple[str, ...] = ()
    time_limit_s: float = 30.0
    start_time_s: float | None = None
    success_message: str = "Targets destroyed."
    failure_message: str = "Time limit exceeded."

    def activate(self) -> list[MissionDirective]:
        super().activate()
        self.start_time_s = None
        return [HUDMessageDirective(f"Objective: {self.title}", level="info", ttl_s=4.0)]

    def update(self, world: WorldView, sim_events: Sequence[object]) -> list[MissionDirective]:
        if self.status is not ObjectiveStatus.ACTIVE:
            return []
        directives: list[MissionDirective] = []
        now = float(world.snapshot().time_s)
        if self.start_time_s is None:
            self.start_time_s = now
        alive = False
        for target_id in self.targets:
            if world.is_alive(target_id):
                alive = True
                break
        if not alive:
            self.status = ObjectiveStatus.SUCCESS
            directives.append(HUDMessageDirective(self.success_message, level="info", ttl_s=6.0))
            return directives
        if (now - float(self.start_time_s)) >= float(self.time_limit_s):
            self.status = ObjectiveStatus.FAILURE
            directives.append(HUDMessageDirective(self.failure_message, level="error", ttl_s=6.0))
        return directives


def _runtime_entity_provider(runtime: RuntimeState) -> Sequence[EntitySnapshot]:
    pose = Pose.from_arrays(runtime.flight.plane_pos, runtime.flight.plane_vel)
    player = EntitySnapshot(
        entity_id="player",
        team="blue",
        alive=True,
        pose=pose,
        tags=("player",),
    )
    return (player,)


def build_runtime_world(
    runtime: RuntimeState,
    time_s: TimeProvider,
    *,
    extra_entities: EntityProvider | None = None,
) -> MissionWorldAdapter:
    def _provider() -> Sequence[EntitySnapshot]:
        base = list(_runtime_entity_provider(runtime))
        if extra_entities is not None:
            base.extend(extra_entities())
        return base

    return MissionWorldAdapter(time_s=time_s, entity_provider=_provider)


def build_time_limit_mission(
    *,
    time_limit_s: float = DEFAULT_TIME_LIMIT_S,
) -> MissionDirector:
    objective = TimeLimitObjective(
        id="time_limit",
        title="Hold position",
        time_limit_s=float(time_limit_s),
        success_message="Mission timer complete.",
    )
    return MissionDirector(objectives=[objective])


def build_destroy_within_time_mission(
    target_ids: Iterable[str],
    *,
    time_limit_s: float = 30.0,
) -> MissionDirector:
    objective = DestroyWithinTimeObjective(
        id="destroy_targets",
        title="Destroy ground targets",
        targets=tuple(target_ids),
        time_limit_s=float(time_limit_s),
    )
    return MissionDirector(objectives=[objective])


@dataclass
class MissionRuntime:
    director: MissionDirector
    world: MissionWorldAdapter
    last_result: MissionTickResult | None = None
    _pending_directives: list[MissionDirective] = field(default_factory=_new_directives, init=False)
    _impact_idx: int = 0
    _explosion_idx: int = 0
    _parachute_idx: int = 0
    _debug_idx: int = 0

    def reset(self) -> None:
        self.director.reset()
        self._pending_directives = list(self.director.start())
        self.last_result = None
        self._impact_idx = 0
        self._explosion_idx = 0
        self._parachute_idx = 0
        self._debug_idx = 0

    def tick(self, runtime: RuntimeState) -> MissionTickResult:
        self.world.refresh()
        sim_events = self._collect_events(runtime)
        result = self.director.tick(self.world, sim_events)
        if self._pending_directives:
            directives = tuple(self._pending_directives) + result.directives
            result = MissionTickResult(
                directives=directives,
                flags=result.flags,
                objective_status=result.objective_status,
                score=result.score,
            )
            self._pending_directives = []
        self.last_result = result
        return result

    def _collect_events(self, runtime: RuntimeState) -> list[object]:
        events: list[object] = []
        impacts = runtime.impacts
        if self._impact_idx < len(impacts):
            events.extend(impacts[self._impact_idx :])
            self._impact_idx = len(impacts)
        explosions = runtime.explosions
        if self._explosion_idx < len(explosions):
            events.extend(explosions[self._explosion_idx :])
            self._explosion_idx = len(explosions)
        parachutes = runtime.parachutes
        if self._parachute_idx < len(parachutes):
            events.extend(parachutes[self._parachute_idx :])
            self._parachute_idx = len(parachutes)
        debug_events = runtime.debug_events
        if self._debug_idx < len(debug_events):
            events.extend(debug_events[self._debug_idx :])
            self._debug_idx = len(debug_events)
        return events
