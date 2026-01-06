from warbits.vislib.blueprints.schema import BlueprintSource, WireframeMesh, VisualBlueprint

def test_blueprint_roundtrip():
    src = BlueprintSource(kind="procedural", name="test", refs=(), license_id="CC0-1.0")
    wf = WireframeMesh(
        vertices_m=[(0.0,0.0,0.0),(1.0,0.0,0.0),(0.0,1.0,0.0)],
        edges=[(0,1),(1,2),(2,0)],
        edge_groups=["silhouette","silhouette","silhouette"]
    )
    bp = VisualBlueprint(entity_id="demo", kind="aircraft", source=src, wireframe=wf)
    bp.validate()
    j = bp.to_json()
    bp2 = VisualBlueprint.from_json(j)
    bp2.validate()
    assert bp2.entity_id == "demo"
    assert bp2.kind == "aircraft"
    assert bp2.wireframe is not None
    assert len(bp2.wireframe.vertices_m) == 3
