from __future__ import annotations

import dataclasses
from typing import Dict, List, Sequence, Tuple, cast

from .directives import MissionDirective
from .objectives import Objective, ObjectiveStatus
from .scoring import ScoreModel
from .timeline import Timeline
from .triggers import Trigger
from .types import WorldView


@dataclasses.dataclass(frozen=True)
class MissionTickResult:
    directives: Tuple[MissionDirective, ...]
    flags: Dict[str, object]
    objective_status: Dict[str, ObjectiveStatus]
    score: float


@dataclasses.dataclass
class MissionDirector:
    """Mission orchestrator.

    - Owns objectives, triggers, flags, timeline and scoring.
    - Deterministic evaluation order.
    - Produces directives for the sim/UI to interpret.

    Typical sim integration:
      result = mission.tick(world_adapter, sim_events)
      sim.apply_directives(result.directives)
      ui.show_messages(result.directives)
    """

    objectives: List[Objective] = dataclasses.field(default_factory=lambda: cast(List[Objective], []))
    triggers: List[Trigger] = dataclasses.field(default_factory=lambda: cast(List[Trigger], []))
    timeline: Timeline = dataclasses.field(default_factory=Timeline)
    flags: Dict[str, object] = dataclasses.field(default_factory=lambda: cast(Dict[str, object], {}))
    score_model: ScoreModel = dataclasses.field(default_factory=ScoreModel)
    active: bool = True

    def reset(self) -> None:
        self.flags = {}
        self.active = True
        self.timeline.reset()
        for o in self.objectives:
            o.status = ObjectiveStatus.INACTIVE
        for t in self.triggers:
            t.enabled = True
            t.has_fired = False

    def start(self) -> List[MissionDirective]:
        # Activate all objectives by default; you can gate them via triggers if you want.
        out: List[MissionDirective] = []
        for o in self.objectives:
            out.extend(o.activate())
        return out

    def tick(self, world: WorldView, sim_events: Sequence[object]) -> MissionTickResult:
        if not self.active:
            return MissionTickResult(
                directives=tuple(),
                flags=dict(self.flags),
                objective_status=self._status_map(),
                score=float(self.score_model.score),
            )

        directives: List[MissionDirective] = []

        # 1) timeline directives
        directives.extend(self.timeline.tick(world))

        # 2) triggers (deterministic order by id)
        for t in sorted(self.triggers, key=lambda tr: (tr.id, tr.repeatable, tr.enabled)):
            directives.extend(t.tick(world, sim_events, self.flags))

        # Apply set_flag directives to flags immediately (so triggers/objectives can depend on them next tick)
        for d in directives:
            if d.kind == "set_flag":
                self.flags[d.payload["flag"]] = d.payload.get("value", None)

        # 3) objectives
        for o in self.objectives:
            directives.extend(o.update(world, sim_events))

        # 4) scoring hook
        self.score_model.on_sim_events(world, sim_events)

        # 5) auto-complete mission if all objectives done (optional)
        if self.objectives and all(o.is_done() for o in self.objectives):
            self.active = False

        return MissionTickResult(
            directives=tuple(directives),
            flags=dict(self.flags),
            objective_status=self._status_map(),
            score=float(self.score_model.score),
        )

    def _status_map(self) -> Dict[str, ObjectiveStatus]:
        return {o.id: o.status for o in self.objectives}
