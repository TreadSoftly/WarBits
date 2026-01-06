from __future__ import annotations

import dataclasses
import json
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np

from .director import MissionDirector
from .objectives import (
    CompositeObjective,
    DestroyEntitiesObjective,
    ReachZoneObjective,
    SurviveObjective,
    TimeLimitObjective,
    Objective,
)
from .triggers import (
    EnterZoneTrigger,
    EventCountTrigger,
    FlagTrigger,
    TimeTrigger,
    Trigger,
)


@dataclasses.dataclass(frozen=True)
class MissionSpec:
    """JSON-serializable mission specification."""
    name: str
    objectives: List[Dict[str, Any]]
    triggers: List[Dict[str, Any]]

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "MissionSpec":
        return MissionSpec(
            name=str(d.get("name", "mission")),
            objectives=list(d.get("objectives", [])),
            triggers=list(d.get("triggers", [])),
        )


def load_mission_spec(path: str) -> MissionSpec:
    with open(path, "r", encoding="utf-8") as f:
        d = json.load(f)
    return MissionSpec.from_dict(d)


def _vec3(x: Any) -> np.ndarray:
    a = np.asarray(x, dtype=np.float64).reshape(3)
    return a


def compile_objective(d: Dict[str, Any]) -> Objective:
    typ = str(d.get("type", "")).lower()
    oid = str(d.get("id", typ))
    title = str(d.get("title", oid))

    if typ == "destroy":
        return DestroyEntitiesObjective(
            id=oid,
            title=title,
            targets=tuple(d.get("targets", [])),
            success_message=str(d.get("success_message", "Targets destroyed.")),
            fail_if_any_missing=bool(d.get("fail_if_any_missing", False)),
        )
    if typ == "survive":
        return SurviveObjective(
            id=oid,
            title=title,
            entity_id=str(d.get("entity_id", "")),
            time_limit_s=d.get("time_limit_s", None),
            success_message=str(d.get("success_message", "Survived.")),
            failure_message=str(d.get("failure_message", "Destroyed.")),
        )
    if typ == "reach_zone":
        return ReachZoneObjective(
            id=oid,
            title=title,
            entity_id=str(d.get("entity_id", "")),
            center_m=_vec3(d.get("center_m", [0, 0, 0])),
            radius_m=float(d.get("radius_m", 500.0)),
            success_message=str(d.get("success_message", "Zone reached.")),
            failure_time_limit_s=d.get("failure_time_limit_s", None),
        )
    if typ == "time":
        return TimeLimitObjective(
            id=oid,
            title=title,
            time_limit_s=float(d.get("time_limit_s", 10.0)),
            success_message=str(d.get("success_message", "Time elapsed.")),
        )
    if typ == "composite":
        mode = str(d.get("mode", "and"))
        children = tuple(compile_objective(cd) for cd in d.get("children", []))
        return CompositeObjective(id=oid, title=title, mode=mode, children=children)

    raise ValueError(f"Unknown objective type: {typ!r}")


def compile_trigger(d: Dict[str, Any]) -> Trigger:
    typ = str(d.get("type", "")).lower()
    tid = str(d.get("id", typ))
    repeatable = bool(d.get("repeatable", False))

    if typ == "time":
        return TimeTrigger(id=tid, repeatable=repeatable, fire_time_s=float(d.get("fire_time_s", 0.0)))
    if typ == "flag":
        return FlagTrigger(id=tid, repeatable=repeatable, flag=str(d.get("flag", "")), equals=d.get("equals", True))
    if typ == "event_count":
        return EventCountTrigger(
            id=tid,
            repeatable=repeatable,
            event_attr=str(d.get("event_attr", "kind")),
            event_value=d.get("event_value", "impact"),
            threshold=int(d.get("threshold", 1)),
        )
    if typ == "enter_zone":
        return EnterZoneTrigger(
            id=tid,
            repeatable=repeatable,
            entity_id=str(d.get("entity_id", "")),
            center_m=_vec3(d.get("center_m", [0, 0, 0])),
            radius_m=float(d.get("radius_m", 500.0)),
        )

    raise ValueError(f"Unknown trigger type: {typ!r}")


def compile_mission(spec: MissionSpec) -> MissionDirector:
    objectives = [compile_objective(o) for o in spec.objectives]
    triggers = [compile_trigger(t) for t in spec.triggers]
    return MissionDirector(objectives=objectives, triggers=triggers)
