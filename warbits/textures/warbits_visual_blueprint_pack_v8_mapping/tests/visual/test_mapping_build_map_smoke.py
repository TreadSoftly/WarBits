from types import SimpleNamespace
from typing import Any, cast

from warbits.visual.mapping.build_map import build_visual_map


def test_build_visual_map_smoke():
    store = SimpleNamespace(
        vehicles={
            "F-15C": {"id": "F-15C", "kind": "aircraft", "length_m": 19.4, "wingspan_m": 13.1},
        },
        weapons={
            "AIM-9L": {"id": "AIM-9L", "kind": "missile", "length_m": 2.87, "diameter_m": 0.127},
        },
    )

    vm = build_visual_map(store=store, blueprints=None, overrides=None)

    assert vm.get("vehicle", "F-15C") is not None
    assert vm.get("weapon", "AIM-9L") is not None

    b_vehicle = cast(Any, vm.get("vehicle", "F-15C"))
    assert b_vehicle.blueprint_id.startswith("proc:")
