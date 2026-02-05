import tempfile
from pathlib import Path

from warbits.visual.blueprint_db import BlueprintDB, write_blueprints_jsonl
from warbits.visual.blueprint_schema import Blueprint
from warbits.visual.registry import VisualRegistry


def test_registry_edges_for_distance():
    bp = Blueprint(
        blueprint_id="vehicle:test",
        kind="vehicle",
        repr="wire3d",
        vertices_m=[(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)],
        edges=[(0, 1), (1, 2)],
        lod_edges={"lod0": ((0, 1), (1, 2)), "lod2": ((0, 1),)},
        tags=[],
        meta={},
    )
    bp.validate()

    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "bp.jsonl"
        write_blueprints_jsonl(p, [bp])

        db = BlueprintDB.load_jsonl(p)
        reg = VisualRegistry(db=db)

        e_near = reg.edges_for_distance("vehicle:test", 10.0)
        e_far = reg.edges_for_distance("vehicle:test", 5000.0)

        assert e_near is not None and len(e_near) >= 1
        assert e_far is not None and len(e_far) >= 1
