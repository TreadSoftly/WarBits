import json
from pathlib import Path
from typing import Any

from warbits.visual.mapping.overrides import apply_overrides, load_overrides
from warbits.visual.mapping.types import VisualBinding, VisualMap


def test_load_overrides_json(tmp_path: Path):
    p = tmp_path / "overrides.json"
    p.write_text(
        json.dumps(
            {
                "vehicle": {"F-15C": {"blueprint_id": "mesh:f15c", "scale": 1.2}},
                "weapon": {"AIM-9L": {"blueprint_id": "mesh:aim9l"}},
            },
            sort_keys=True,
        )
    )
    ov = load_overrides(p)
    assert ov["vehicle"]["F-15C"]["blueprint_id"] == "mesh:f15c"


def test_apply_overrides():
    vm = VisualMap()
    vm.set("vehicle", "F-15C", VisualBinding(blueprint_id="proc:aircraft"))
    vm.set("weapon", "AIM-9L", VisualBinding(blueprint_id="proc:missile"))

    overrides: dict[str, Any] = {
        "vehicle": {"F-15C": {"blueprint_id": "mesh:f15c", "scale": 1.3}},
        "weapon": {},
    }
    vm2 = apply_overrides(vm, overrides)
    b = vm2.get("vehicle", "F-15C")
    assert b is not None
    assert b.blueprint_id == "mesh:f15c"
    assert abs((b.scale or 1.0) - 1.3) < 1e-9
