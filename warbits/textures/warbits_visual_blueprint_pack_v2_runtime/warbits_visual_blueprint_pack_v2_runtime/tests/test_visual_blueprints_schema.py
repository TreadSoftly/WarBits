import json
from warbits.visual.blueprint_schema import Blueprint


def test_blueprint_roundtrip_wire3d():
    bp = Blueprint(
        blueprint_id="vehicle:f16",
        kind="vehicle",
        repr="wire3d",
        vertices_m=[(0.0,0.0,0.0),(1.0,0.0,0.0),(0.0,1.0,0.0)],
        edges=[(0,1),(1,2)],
        lod_edges={"lod0":[(0,1),(1,2)], "lod1":[(0,1)]},
        tags=["jet","test"],
        meta={"source":"unit"},
    )
    bp.validate()

    obj = bp.to_json_obj()
    s = json.dumps(obj)
    bp2 = Blueprint.from_json_obj(json.loads(s))
    bp2.validate()

    assert bp2.blueprint_id == bp.blueprint_id
    assert bp2.repr == "wire3d"
    assert len(bp2.vertices_m) == 3
    assert len(bp2.select_edges("lod1")) == 1
