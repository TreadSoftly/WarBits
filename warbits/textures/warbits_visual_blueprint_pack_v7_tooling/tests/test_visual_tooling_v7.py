from pathlib import Path

from warbits.visual.blueprint_schema import Blueprint
from warbits.visual.budgets import check_budget
from warbits.visual.metrics import compute_metrics
from warbits.visual.tools.atlas import render_atlas


def _make_tiny_blueprint(blueprint_id: str = "unit_test::cube", edges_multiplier: int = 1) -> Blueprint:
    # Simple cube-ish wireframe
    verts = [
        (-1.0, -1.0, -1.0),
        (1.0, -1.0, -1.0),
        (1.0, 1.0, -1.0),
        (-1.0, 1.0, -1.0),
        (-1.0, -1.0, 1.0),
        (1.0, -1.0, 1.0),
        (1.0, 1.0, 1.0),
        (-1.0, 1.0, 1.0),
    ]
    base_edges = [
        (0, 1),
        (1, 2),
        (2, 3),
        (3, 0),
        (4, 5),
        (5, 6),
        (6, 7),
        (7, 4),
        (0, 4),
        (1, 5),
        (2, 6),
        (3, 7),
    ]
    edges = base_edges * max(1, edges_multiplier)

    return Blueprint(
        blueprint_id=blueprint_id,
        kind="vehicle",
        repr="wireframe3d",
        vertices_m=verts,
        edges=edges,
        lod_edges={
            "lod0": tuple(edges),
            "lod1": tuple(base_edges),
            "lod2": ((0, 1), (1, 2), (2, 3), (3, 0)),  # silhouette only
        },
        outline2d=None,
        tags=["aircraft"],
        meta={"name": "UNIT_TEST_CUBE"},
    )


def test_metrics_bbox_and_counts():
    bp = _make_tiny_blueprint()
    m = compute_metrics(bp, lod="lod0")
    assert m.vertices == 8
    assert m.edges == 12
    assert m.bbox_min == (-1.0, -1.0, -1.0)
    assert m.bbox_max == (1.0, 1.0, 1.0)


def test_budget_pass_default():
    bp = _make_tiny_blueprint()
    chk = check_budget(bp, lod="lod0")
    assert chk.ok, chk.reasons


def test_budget_fail_when_edges_excessive():
    bp = _make_tiny_blueprint(edges_multiplier=200)  # 2400 edges
    chk = check_budget(bp, lod="lod0")
    assert not chk.ok
    assert any("edges" in r for r in chk.reasons)


def test_atlas_smoke(tmp_path: Path):
    bp = _make_tiny_blueprint()
    out = tmp_path / "atlas.png"
    render_atlas([bp], out, view="iso", lod="lod0", max_items=1, cols=1)
    assert out.exists()
    assert out.stat().st_size > 0
