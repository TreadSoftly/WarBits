from __future__ import annotations

from typing import TYPE_CHECKING, Any, List, Tuple

from ..blueprints.schema import WireframeMesh
from ..style.wireframe import WireframeStyle


class _Line3DCollection:
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        pass


if TYPE_CHECKING:
    Line3DCollection = _Line3DCollection
else:
    from mpl_toolkits.mplot3d.art3d import Line3DCollection  # type: ignore[reportMissingTypeStubs]


def _segments(
    vertices: List[Tuple[float, float, float]],
    edges: List[Tuple[int, int]],
) -> List[List[Tuple[float, float, float]]]:
    segs: List[List[Tuple[float, float, float]]] = []
    for a, b in edges:
        segs.append([vertices[a], vertices[b]])
    return segs


def add_wireframe3d(ax: Any, mesh: WireframeMesh, style: WireframeStyle) -> List[Line3DCollection]:
    """Add a wireframe mesh to a Matplotlib 3D axis.

    Returns the created Line3DCollection objects (for later updates/removal).
    """
    mesh.validate()

    artists: List[Line3DCollection] = []

    # Optionally draw glow by drawing multiple passes behind the main line set.
    if style.glow is not None and style.glow.passes > 0:
        for i in range(style.glow.passes):
            width = style.silhouette_width * (1.0 + style.glow.outer_width_mul * (i + 1) / style.glow.passes)
            alpha = style.glow.outer_alpha
            lc = Line3DCollection(
                _segments(mesh.vertices_m, mesh.edges),
                colors=style.color,
                linewidths=width,
                alpha=alpha,
            )
            ax.add_collection3d(lc)
            artists.append(lc)

    lc_main = Line3DCollection(
        _segments(mesh.vertices_m, mesh.edges),
        colors=style.color,
        linewidths=style.silhouette_width,
        alpha=style.alpha,
    )
    ax.add_collection3d(lc_main)
    artists.append(lc_main)

    return artists
    return artists
