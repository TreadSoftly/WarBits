from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from .imports import require_panda3d
from .style import NEON_GREEN, WireframeP3DStyle

NDArrayFloat = NDArray[np.float32]


@dataclass
class LineBatchStats:
    max_segments: int
    active_segments: int = 0
    last_upload_bytes: int = 0


class DynamicLineBatch:
    """A single dynamic line batch: one Geom, updated every frame.

    This is the v5 Panda3D “fast path” building block.

    Strategy:
    - Pre-allocate a V3 vertex buffer for max_segments*2 vertices.
    - Build a GeomLines primitive once with fixed indices.
    - Each frame: upload new vertex positions into the buffer.

    Notes:
    - We keep a fixed number of line segments. Extra segments become zero-length.
    - This avoids rebuilding primitives per frame (which would hitch).
    """

    def __init__(self, *, max_segments: int, style: WireframeP3DStyle = NEON_GREEN, name: str = "wireframe_lines"):
        if max_segments <= 0:
            raise ValueError("max_segments must be > 0")
        self.max_segments = int(max_segments)
        self.max_vertices = self.max_segments * 2
        self.style = style
        self.name = name

        self._p3d, _ = require_panda3d()
        p3d = self._p3d

        # Vertex format: positions only (V3)
        self._format = p3d.GeomVertexFormat.getV3()
        self._vdata = p3d.GeomVertexData(name, self._format, p3d.Geom.UHDynamic)
        self._vdata.setNumRows(self.max_vertices)

        # Create a GeomLines primitive with fixed indices.
        prim = p3d.GeomLines(p3d.Geom.UHStatic)
        # Each segment uses two vertices in order: (0,1), (2,3), ...
        for i in range(self.max_segments):
            a = 2 * i
            b = 2 * i + 1
            prim.addVertices(a, b)
            prim.closePrimitive()

        geom = p3d.Geom(self._vdata)
        geom.addPrimitive(prim)

        node = p3d.GeomNode(name)
        node.addGeom(geom)

        self.nodepath = p3d.NodePath(node)

        # Internal staging buffer (numpy float32) to avoid allocations.
        self._buf = np.zeros((self.max_vertices, 3), dtype=np.float32)

        self.stats = LineBatchStats(max_segments=self.max_segments)
        self._apply_style()

    def _apply_style(self) -> None:
        p3d = self._p3d
        self.nodepath.setColor(*self.style.color)
        self.nodepath.setRenderModeThickness(self.style.line_thickness)

        if self.style.unlit:
            self.nodepath.setLightOff(1)

        if self.style.additive_blend:
            self.nodepath.setTransparency(p3d.TransparencyAttrib.M_alpha)
            self.nodepath.setAttrib(p3d.ColorBlendAttrib.make(p3d.ColorBlendAttrib.MAdd))

        if self.style.overlay:
            # Render on top (debug). You may disable depth write for HUD-like overlay.
            self.nodepath.setDepthTest(False)
            self.nodepath.setDepthWrite(False)

    # ---------------------------------------------------------------------
    # Update API
    # ---------------------------------------------------------------------

    def begin(self) -> NDArrayFloat:
        """Return the internal staging buffer (shape: (max_vertices,3)).

        Fill the first N rows with your line endpoints, then call commit(active_segments).
        """
        return self._buf

    def commit(self, *, active_segments: int) -> None:
        """Upload the staging buffer to the GPU."""
        nseg = int(active_segments)
        if nseg < 0 or nseg > self.max_segments:
            raise ValueError(f"active_segments must be in [0,{self.max_segments}]")

        need = nseg * 2
        if need < self.max_vertices:
            # Make remaining vertices degenerate segments by duplicating last.
            last = self._buf[need - 1] if need > 0 else np.zeros(3, dtype=np.float32)
            self._buf[need:] = last

        handle = self._vdata.modifyArray(0).modifyHandle()
        raw = self._buf.tobytes()
        handle.setData(raw)

        self.stats.active_segments = nseg
        self.stats.last_upload_bytes = len(raw)

    def update_segments(self, segments_world: NDArrayFloat) -> None:
        """Convenience: update from segments shaped (N,2,3)."""
        seg = np.asarray(segments_world, dtype=np.float32)
        if seg.ndim != 3 or seg.shape[1:] != (2, 3):
            raise ValueError(f"segments_world must have shape (N,2,3). Got {seg.shape}")
        n = int(seg.shape[0])
        if n > self.max_segments:
            raise ValueError(f"Too many segments: {n} > max_segments {self.max_segments}")
        flat = seg.reshape(n * 2, 3)
        buf = self.begin()
        buf[: n * 2] = flat
        self.commit(active_segments=n)

    def remove(self) -> None:
        """Detach from scene graph."""
        self.nodepath.removeNode()
