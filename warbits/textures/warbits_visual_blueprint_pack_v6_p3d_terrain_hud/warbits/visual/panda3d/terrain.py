"""warbits.visual.panda3d.terrain

Panda3D terrain helpers intended for the WarBits visual language:

- Dark, readable heightfield surface (cheap to render)
- Optional neon wire grid overlay (Matplotlib-ish 'sim wire' vibe)
- No per-frame allocations: build once, then reuse

Design goals:
- Extremely high FPS: static geom + optional sparse grid lines
- Deterministic visuals from deterministic input heights
- No Blender required (pure Python + Panda3D)

This module is safe to import even when Panda3D is not installed.
Panda3D is only required at runtime when constructing nodes.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Iterable, Optional, Tuple

import numpy as np

from .imports import is_panda3d_available, require_panda3d
from .line_batch import DynamicLineBatch
from .style import WireframeP3DStyle

if TYPE_CHECKING:  # pragma: no cover
    # Only for type checkers; we avoid importing Panda3D at import time.
    from panda3d.core import NodePath  # type: ignore


RGBA = Tuple[float, float, float, float]


@dataclass(frozen=True)
class HeightfieldSpec:
    """Defines a heightfield in world space.

    heights: 2D array (ny, nx) of height samples (meters, or already scaled).
    x0, y0: world origin (meters) at heights[0, 0]
    dx, dy: spacing between samples (meters)
    z_scale: multiplier applied to heights (default 1.0)
    """

    heights: np.ndarray
    x0: float
    y0: float
    dx: float
    dy: float
    z_scale: float = 1.0


@dataclass(frozen=True)
class TerrainStyle:
    """Visual style for terrain surface and optional wire overlay."""

    # Surface fill color (very dark by default).
    surface_rgba: RGBA = (0.03, 0.03, 0.035, 1.0)

    # If True, slightly vary brightness with altitude to increase depth cues.
    shade_by_height: bool = True
    shade_strength: float = 0.20  # small, keep it subtle

    # Optional wire grid overlay.
    grid_enabled: bool = True
    grid_stride: int = 6  # larger stride => fewer segments => faster
    grid_rgba: RGBA = (0.20, 1.00, 0.20, 0.14)
    grid_thickness: float = 1.0
    grid_antialias: bool = False
    grid_depth_test: bool = True


def _safe_norm(v: np.ndarray, eps: float = 1e-9) -> np.ndarray:
    n = float(np.linalg.norm(v))
    if n < eps:
        return np.array([0.0, 0.0, 1.0], dtype=np.float32)
    return (v / n).astype(np.float32)


def compute_vertex_normals(heights: np.ndarray, dx: float, dy: float) -> np.ndarray:
    """Approximate per-vertex normals from a heightfield.

    Returns: normals (ny, nx, 3) float32, unit length.

    Notes:
    - Uses numpy.gradient which is fast and stable.
    - Normal convention: z-up (0,0,1).
    """
    h = np.asarray(heights, dtype=np.float32)
    # gradient returns dH/dy, dH/dx by default for 2D
    dh_dy, dh_dx = np.gradient(h, dy, dx)
    nx = -dh_dx
    ny = -dh_dy
    nz = np.ones_like(h, dtype=np.float32)
    n = np.stack([nx, ny, nz], axis=-1)
    mag = np.linalg.norm(n, axis=-1, keepdims=True)
    n = n / (mag + 1e-9)
    return n.astype(np.float32)


def compute_height_shaded_colors(
    heights: np.ndarray, base_rgba: RGBA, strength: float
) -> np.ndarray:
    """Return per-vertex RGBA colors (ny, nx, 4) based on altitude.

    This is intentionally subtle: it's there to make terrain readable without
    turning into a 'pretty shader' project.
    """
    h = np.asarray(heights, dtype=np.float32)
    hmin = float(np.min(h))
    hmax = float(np.max(h))
    span = max(hmax - hmin, 1e-6)
    t = (h - hmin) / span  # 0..1

    br, bg, bb, ba = base_rgba
    # Keep the base very dark and add a slight brightness lift with altitude.
    lift = (t * float(strength) * 0.10).astype(np.float32)
    r = np.clip(br + lift, 0.0, 1.0)
    g = np.clip(bg + lift, 0.0, 1.0)
    b = np.clip(bb + lift, 0.0, 1.0)
    a = np.full_like(r, ba, dtype=np.float32)
    return np.stack([r, g, b, a], axis=-1).astype(np.float32)


def build_wire_grid_segments(spec: HeightfieldSpec, stride: int) -> np.ndarray:
    """Build line segments for a sparse wire grid overlay.

    Returns segments shaped (N, 2, 3), dtype float32, in world coordinates.
    """
    stride = max(int(stride), 1)
    h = np.asarray(spec.heights, dtype=np.float32) * float(spec.z_scale)
    ny, nx = h.shape

    # Precompute world X and Y coordinates for grid indices (cheap).
    xs = spec.x0 + np.arange(nx, dtype=np.float32) * float(spec.dx)
    ys = spec.y0 + np.arange(ny, dtype=np.float32) * float(spec.dy)

    segs: list[np.ndarray] = []

    # Rows (constant y, varying x)
    for j in range(0, ny, stride):
        y = ys[j]
        # Connect points at stride step to reduce segment count.
        for i in range(0, nx - stride, stride):
            p0 = np.array([xs[i], y, h[j, i]], dtype=np.float32)
            p1 = np.array([xs[i + stride], y, h[j, i + stride]], dtype=np.float32)
            segs.append(np.stack([p0, p1], axis=0))

    # Cols (constant x, varying y)
    for i in range(0, nx, stride):
        x = xs[i]
        for j in range(0, ny - stride, stride):
            p0 = np.array([x, ys[j], h[j, i]], dtype=np.float32)
            p1 = np.array([x, ys[j + stride], h[j + stride, i]], dtype=np.float32)
            segs.append(np.stack([p0, p1], axis=0))

    if not segs:
        return np.zeros((0, 2, 3), dtype=np.float32)
    return np.stack(segs, axis=0).astype(np.float32)


def build_static_heightfield_node(
    spec: HeightfieldSpec,
    *,
    style: TerrainStyle = TerrainStyle(),
    name: str = "terrain",
):
    """Build a static terrain surface as a Panda3D node.

    Returns: NodePath (requires Panda3D).

    Performance:
    - UHStatic vertex/index buffers
    - Build once at startup
    - Suitable for very high FPS with reasonable grid sizes.
    """
    p3d = require_panda3d()

    heights = np.asarray(spec.heights, dtype=np.float32) * float(spec.z_scale)
    ny, nx = heights.shape

    normals = compute_vertex_normals(heights, float(spec.dx), float(spec.dy))
    if style.shade_by_height:
        colors = compute_height_shaded_colors(heights, style.surface_rgba, style.shade_strength)
    else:
        colors = np.zeros((ny, nx, 4), dtype=np.float32)
        colors[..., 0] = style.surface_rgba[0]
        colors[..., 1] = style.surface_rgba[1]
        colors[..., 2] = style.surface_rgba[2]
        colors[..., 3] = style.surface_rgba[3]

    vformat = p3d.GeomVertexFormat.getV3n3c4()
    vdata = p3d.GeomVertexData(name, vformat, p3d.Geom.UHStatic)
    vdata.setNumRows(nx * ny)

    vw = p3d.GeomVertexWriter(vdata, "vertex")
    nw = p3d.GeomVertexWriter(vdata, "normal")
    cw = p3d.GeomVertexWriter(vdata, "color")

    # Emit vertices row-major.
    for j in range(ny):
        y = spec.y0 + float(j) * float(spec.dy)
        for i in range(nx):
            x = spec.x0 + float(i) * float(spec.dx)
            z = float(heights[j, i])
            vw.addData3f(x, y, z)

            n = normals[j, i]
            nw.addData3f(float(n[0]), float(n[1]), float(n[2]))

            c = colors[j, i]
            cw.addData4f(float(c[0]), float(c[1]), float(c[2]), float(c[3]))

    prim = p3d.GeomTriangles(p3d.Geom.UHStatic)
    # Emit triangles for each cell.
    # Index mapping: idx = j*nx + i
    for j in range(ny - 1):
        row0 = j * nx
        row1 = (j + 1) * nx
        for i in range(nx - 1):
            v0 = row0 + i
            v1 = row0 + i + 1
            v2 = row1 + i + 1
            v3 = row1 + i
            prim.addVertices(v0, v1, v2)
            prim.addVertices(v0, v2, v3)

    geom = p3d.Geom(vdata)
    geom.addPrimitive(prim)
    node = p3d.GeomNode(name)
    node.addGeom(geom)
    np_node = p3d.NodePath(node)
    np_node.setTwoSided(True)
    # Optional: keep terrain subtle.
    np_node.setTransparency(p3d.TransparencyAttrib.MNone)
    return np_node


class P3DTerrain:
    """Convenience wrapper: static surface + optional wire grid overlay."""

    def __init__(
        self,
        parent,
        spec: HeightfieldSpec,
        *,
        style: TerrainStyle = TerrainStyle(),
        surface_name: str = "terrain_surface",
        grid_name: str = "terrain_grid",
    ):
        self.spec = spec
        self.style = style

        self.surface = build_static_heightfield_node(spec, style=style, name=surface_name)
        self.surface.reparentTo(parent)

        self.grid: Optional[DynamicLineBatch] = None
        if style.grid_enabled:
            segs = build_wire_grid_segments(spec, stride=style.grid_stride)

            line_style = WireframeP3DStyle(
                line_rgba=style.grid_rgba,
                thickness=float(style.grid_thickness),
                antialias=bool(style.grid_antialias),
                depth_test=bool(style.grid_depth_test),
                additive=False,
            )
            self.grid = DynamicLineBatch(int(segs.shape[0]), style=line_style, name=grid_name)
            self.grid.nodepath.reparentTo(parent)
            self.grid.update_segments(segs)

    def set_visible(self, visible: bool) -> None:
        if visible:
            self.surface.show()
            if self.grid is not None:
                self.grid.nodepath.show()
        else:
            self.surface.hide()
            if self.grid is not None:
                self.grid.nodepath.hide()

    def destroy(self) -> None:
        self.surface.removeNode()
        if self.grid is not None:
            self.grid.nodepath.removeNode()
            self.grid = None
