from typing import Any, cast

from warbits.visual.blueprint_db import BlueprintDB
from warbits.visual.blueprint_schema import Blueprint
from warbits.visual.mapping.rules import resolve_visual_binding


def test_resolve_prefers_mesh_blueprint_when_available():
    bp = Blueprint(
        blueprint_id="vehicle:f-15c",
        kind="vehicle",
        vertices_m=((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)),
        edges=((0, 1), (1, 2), (2, 0)),
    )
    db = BlueprintDB(by_id={"vehicle:f-15c": bp})

    b = resolve_visual_binding(
        entity_kind="vehicle",
        entity_id="F-15C",
        spec={
            "name": "F-15C",
            "kind": "aircraft",
            "length_m": 19.4,
            "wingspan_m": 13.1,
            "height_m": 5.6,
        },
        blueprints=db,
        overrides=None,
    )

    b_any = cast(Any, b)
    assert b_any.source == "mesh"
    assert b_any.blueprint_id == "vehicle:f-15c"


def test_resolve_falls_back_to_procedural():
    db = BlueprintDB(by_id={})

    b = resolve_visual_binding(
        entity_kind="weapon",
        entity_id="AIM-9L",
        spec={"name": "AIM-9L", "kind": "missile", "length_m": 2.9},
        blueprints=db,
        overrides=None,
    )

    b_any = cast(Any, b)
    assert b_any.source == "procedural"
    assert b_any.blueprint_id.startswith("proc:")
