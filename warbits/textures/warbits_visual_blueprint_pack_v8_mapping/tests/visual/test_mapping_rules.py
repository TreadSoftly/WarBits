from warbits.visual.mapping.rules import resolve_visual_binding


def test_resolve_prefers_mesh_blueprint_when_available():
    blueprint_ids = [
        "vehicle:f-15c",
        "weapon:aim-9l",
        "mesh:other",
    ]

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
        blueprint_ids=blueprint_ids,
        overrides=None,
    )

    assert b.source == "mesh"
    assert b.blueprint_id == "vehicle:f-15c"


def test_resolve_falls_back_to_procedural():
    blueprint_ids = ["mesh:other"]

    b = resolve_visual_binding(
        entity_kind="weapon",
        entity_id="AIM-9L",
        spec={"name": "AIM-9L", "kind": "missile", "length_m": 2.9},
        blueprint_ids=blueprint_ids,
        overrides=None,
    )

    assert b.source == "procedural"
    assert b.blueprint_id.startswith("proc:")
