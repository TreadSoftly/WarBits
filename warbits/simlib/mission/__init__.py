"""WarBits SmartLib - Mission

Renderer-agnostic mission/objective/trigger logic that can sit on top of a simulation.

Core idea:
  - Simulation produces world state + sim events (impacts/explosions/etc).
  - MissionDirector consumes them and produces mission directives:
      - messages
      - spawns
      - objective status updates
      - flags

This separation keeps your simulation deterministic and testable.
"""

from .types import Pose, Team, EntitySnapshot, WorldSnapshot
from .directives import (
    MissionDirective,
    HUDMessageDirective,
    SetFlagDirective,
    SpawnDirective,
    DespawnDirective,
)
from .objectives import (
    ObjectiveStatus,
    Objective,
    DestroyEntitiesObjective,
    SurviveObjective,
    ReachZoneObjective,
    TimeLimitObjective,
    CompositeObjective,
)
from .triggers import Trigger, TimeTrigger, FlagTrigger, EventCountTrigger, EnterZoneTrigger
from .director import MissionDirector, MissionTickResult
from .dsl import MissionSpec, load_mission_spec, compile_mission
from .scoring import ScoreEvent, ScoreModel
from .timeline import Timeline

__all__ = [
    "Pose",
    "Team",
    "EntitySnapshot",
    "WorldSnapshot",
    "MissionDirective",
    "HUDMessageDirective",
    "SetFlagDirective",
    "SpawnDirective",
    "DespawnDirective",
    "ObjectiveStatus",
    "Objective",
    "DestroyEntitiesObjective",
    "SurviveObjective",
    "ReachZoneObjective",
    "TimeLimitObjective",
    "CompositeObjective",
    "Trigger",
    "TimeTrigger",
    "FlagTrigger",
    "EventCountTrigger",
    "EnterZoneTrigger",
    "MissionDirector",
    "MissionTickResult",
    "MissionSpec",
    "load_mission_spec",
    "compile_mission",
    "ScoreEvent",
    "ScoreModel",
    "Timeline",
]
