import matplotlib

matplotlib.use("Agg")  # headless

from typing import Any, cast

import matplotlib.pyplot as plt

from warbits.visual.blueprint_db import BlueprintDB
from warbits.visual.blueprint_schema import Blueprint
from warbits.visual.mpl.blueprint_layer import BlueprintInstance, MPLBlueprintLayer
from warbits.visual.registry import BlueprintRegistry


def test_mpl_blueprint_layer_renders_without_exceptions():
    # Simple tetrahedron wireframe
    verts = (
        (0.0, 0.0, 0.0),
        (1.0, 0.0, 0.0),
        (0.0, 1.0, 0.0),
        (0.0, 0.0, 1.0),
    )
    edges = (
        (0, 1),
        (0, 2),
        (0, 3),
        (1, 2),
        (1, 3),
        (2, 3),
    )

    bp = Blueprint(blueprint_id="tetra", kind="vehicle", vertices_m=verts, edges=edges, lod_edges={})
    db = BlueprintDB(by_id={"tetra": bp})
    registry = BlueprintRegistry(db)

    plt_any = cast(Any, plt)
    fig = plt_any.figure(figsize=(6, 4))
    ax = fig.add_subplot(111, projection="3d")

    layer = MPLBlueprintLayer(ax, registry, enable_detail=True)

    inst = BlueprintInstance(blueprint_id="tetra", position_m=(0.0, 0.0, 0.0), role="friendly")
    layer.update([inst], camera_pos=(0.0, 0.0, 0.0))

    # Ensure outline segments exist
    outline = layer._artists["friendly"]["outline"]  # type: ignore[reportPrivateUsage]
    assert len(outline._segments3d) == len(edges)

    # Force a draw (Agg)
    fig.canvas.draw()

    # Force a draw (Agg)
    fig.canvas.draw()
