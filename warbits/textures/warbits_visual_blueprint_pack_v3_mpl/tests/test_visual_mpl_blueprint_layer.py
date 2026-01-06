import matplotlib
matplotlib.use("Agg")  # headless

import numpy as np
import matplotlib.pyplot as plt

from warbits.visual.blueprint_schema import Blueprint
from warbits.visual.blueprint_db import BlueprintDB
from warbits.visual.registry import BlueprintRegistry
from warbits.visual.mpl.blueprint_layer import BlueprintInstance, MPLBlueprintLayer


def test_mpl_blueprint_layer_renders_without_exceptions():
    # Simple tetrahedron wireframe
    verts = [
        [0.0, 0.0, 0.0],
        [1.0, 0.0, 0.0],
        [0.0, 1.0, 0.0],
        [0.0, 0.0, 1.0],
    ]
    edges = [
        [0, 1],
        [0, 2],
        [0, 3],
        [1, 2],
        [1, 3],
        [2, 3],
    ]

    bp = Blueprint(id="tetra", vertices=verts, edges=edges, lod_edges={}, anchors={})
    db = BlueprintDB(by_id={"tetra": bp})
    registry = BlueprintRegistry(db)

    fig = plt.figure(figsize=(6, 4))
    ax = fig.add_subplot(111, projection="3d")

    layer = MPLBlueprintLayer(ax, registry, enable_detail=True)

    inst = BlueprintInstance(blueprint_id="tetra", position_m=(0.0, 0.0, 0.0), role="friendly")
    layer.update([inst], camera_pos=(0.0, 0.0, 0.0))

    # Ensure outline segments exist
    outline = layer._artists["friendly"]["outline"]
    assert len(outline._segments3d) == len(edges)

    # Force a draw (Agg)
    fig.canvas.draw()
