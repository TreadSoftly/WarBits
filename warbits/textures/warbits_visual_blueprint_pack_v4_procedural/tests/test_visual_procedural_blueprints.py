from typing import Sequence

from warbits.visual.defaults import build_default_blueprint_db
from warbits.visual.procedural.aircraft import JetParams, build_jet_blueprint
from warbits.visual.procedural.ground import TankParams, build_tank_blueprint
from warbits.visual.procedural.ordnance import BombParams, MissileParams, build_bomb_blueprint, build_missile_blueprint
from warbits.visual.visual_resolver import VisualResolver


def _assert_edges_in_range(vertices: Sequence[Sequence[float]], edges: Sequence[tuple[int, int]]) -> None:
    n = len(vertices)
    assert n > 0
    assert len(edges) > 0
    for a, b in edges:
        assert 0 <= int(a) < n
        assert 0 <= int(b) < n
        assert int(a) != int(b)


def test_procedural_jet_blueprint_valid():
    bp = build_jet_blueprint("proc:test:jet", JetParams(length_m=16.0, wingspan_m=10.5, height_m=4.5))
    assert bp.kind == "aircraft"
    assert len(bp.vertices_m[0]) == 3
    _assert_edges_in_range(bp.vertices_m, bp.edges)
    assert "silhouette" in bp.lod_edges
    assert "low" in bp.lod_edges
    _assert_edges_in_range(bp.vertices_m, bp.lod_edges["silhouette"])
    _assert_edges_in_range(bp.vertices_m, bp.lod_edges["low"])


def test_procedural_tank_blueprint_valid():
    bp = build_tank_blueprint("proc:test:tank", TankParams(length_m=7.0, width_m=3.6, height_m=2.5))
    assert bp.kind == "ground"
    _assert_edges_in_range(bp.vertices_m, bp.edges)
    assert "silhouette" in bp.lod_edges
    assert "low" in bp.lod_edges


def test_procedural_ordnance_blueprints_valid():
    m = build_missile_blueprint("proc:test:missile", MissileParams(length_m=3.6, diameter_m=0.24))
    b = build_bomb_blueprint("proc:test:bomb", BombParams(length_m=2.8, diameter_m=0.35))
    assert m.kind == "ordnance"
    assert b.kind == "ordnance"
    _assert_edges_in_range(m.vertices_m, m.edges)
    _assert_edges_in_range(b.vertices_m, b.edges)


def test_visual_resolver_generates_and_registers():
    db = build_default_blueprint_db()
    resolver = VisualResolver(db)

    spec: dict[str, object] = {
        "name": "Test Fighter",
        "visual_kind": "aircraft",
        "length_m": 15.2,
        "wingspan_m": 10.1,
        "height_m": 4.6,
        "twin_tail": True,
    }

    bp = resolver.resolve("vehicle:test_fighter", spec)
    assert bp.blueprint_id == "vehicle:test_fighter"
    # Should now be in the DB
    assert db.get("vehicle:test_fighter") is not None
    # Should now be in the DB
    assert db.get("vehicle:test_fighter") is not None
    # Should now be in the DB
    assert db.get("vehicle:test_fighter") is not None
