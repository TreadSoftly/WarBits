import matplotlib
matplotlib.use("Agg")  # headless

import numpy as np
import matplotlib.pyplot as plt

from warbits.visual.blueprint_db import BlueprintDB
from warbits.visual.blueprint_schema import Blueprint
from warbits.visual.registry import BlueprintRegistry
from warbits.visual.mpl.blueprint_layer import MPLBlueprintLayer, BlueprintInstance


def _db_put(db: BlueprintDB, bp: Blueprint) -> None:
    # Support both old/new DB flavors.
    if hasattr(db, "register"):
        db.register(bp)  # type: ignore[attr-defined]
        return
    db.by_id[bp.blueprint_id] = bp


def test_mpl_blueprint_layer_renders_one_instance():
    # Simple tetrahedron wireframe
    verts = np.array([
        [0.0, 0.0, 0.0],
        [1.0, 0.0, 0.0],
        [0.5, 1.0, 0.0],
        [0.5, 0.5, 1.0],
    ], dtype=float)

    edges = [
        (0, 1), (1, 2), (2, 0),  # base triangle
        (0, 3), (1, 3), (2, 3),  # sides
    ]

    bp = Blueprint(
        blueprint_id="tetra",
        kind="test",
        tags=["test", "wireframe"],
        vertices_m=verts,
        edges=edges,
        lod_edges={"silhouette": edges},
        meta={"source": "unit_test"},
    )

    db = BlueprintDB.empty() if hasattr(BlueprintDB, "empty") else BlueprintDB(by_id={})  # type: ignore
    _db_put(db, bp)

    registry = BlueprintRegistry(db)
    fig = plt.figure(figsize=(4, 3))
    ax = fig.add_subplot(111, projection="3d")

    layer = MPLBlueprintLayer(ax=ax, registry=registry)

    inst = BlueprintInstance(
        blueprint_id="tetra",
        position_m=(0.0, 0.0, 0.0),
        rotation_mat=np.eye(3, dtype=float),
        scale=1.0,
        role="neutral",
    )

    layer.update([inst], camera_pos=(0.0, 0.0, 10.0))

    assert "neutral" in layer._artists
    assert len(layer._artists["neutral"]) > 0

    # Clear should not error
    layer.clear()
