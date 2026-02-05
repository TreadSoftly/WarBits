"""Panda3D 2D HUD overlay renderer.

This module is optional. If Panda3D isn't installed, importing will fail.

We focus on *performance*: we avoid recreating nodes every frame.
Lines are drawn with a dynamic Geom in aspect2d.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Optional, Tuple

import numpy as np

from ..hud.types import HudBox, HudCircle, HudDrawList, HudLine, HudText


class _P3DGeom:
    UHDynamic: int = 0

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        pass

    def add_primitive(self, prim: Any) -> None:
        pass


class _P3DGeomLines:
    UHDynamic: int = 0

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        pass

    def add_vertices(self, v0: int, v1: int) -> None:
        pass

    def close_primitive(self) -> None:
        pass


class _P3DGeomNode:
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        pass

    def add_geom(self, geom: Any) -> None:
        pass


class _P3DGeomVertexData:
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        pass

    def set_num_rows(self, rows: int) -> None:
        pass


class _P3DGeomVertexFormat:
    @staticmethod
    def get_v3c4() -> Any:
        return None


class _P3DGeomVertexWriter:
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        pass

    def set_row(self, row: int) -> None:
        pass

    def add_data3(self, x: float, y: float, z: float) -> None:
        pass

    def add_data4(self, r: float, g: float, b: float, a: float) -> None:
        pass


class _P3DNodePath:
    def attach_new_node(self, node: Any) -> Any:
        return self

    def set_transparency(self, mode: Any) -> None:
        pass


class _P3DTransparencyAttrib:
    M_alpha: int = 0


class _P3DOnscreenText:
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        pass

    def setText(self, text: str) -> None:
        pass

    def setPos(self, x: float, y: float) -> None:
        pass

    def setFg(self, rgba: Tuple[float, float, float, float]) -> None:
        pass

    def setScale(self, scale: float) -> None:
        pass

    def reparentTo(self, parent: Any) -> None:
        pass

    def hide(self) -> None:
        pass

    def show(self) -> None:
        pass


if TYPE_CHECKING:
    Geom = _P3DGeom
    GeomLines = _P3DGeomLines
    GeomNode = _P3DGeomNode
    GeomVertexData = _P3DGeomVertexData
    GeomVertexFormat = _P3DGeomVertexFormat
    GeomVertexWriter = _P3DGeomVertexWriter
    NodePath = _P3DNodePath
    TransparencyAttrib = _P3DTransparencyAttrib
    OnscreenText = _P3DOnscreenText
else:
    try:
        from direct.gui.OnscreenText import OnscreenText  # type: ignore[reportMissingTypeStubs]
        from panda3d.core import Geom  # type: ignore[reportMissingTypeStubs]
        from panda3d.core import (
            GeomLines,
            GeomNode,
            GeomVertexData,
            GeomVertexFormat,
            GeomVertexWriter,
            TransparencyAttrib,
        )
    except Exception as e:  # pragma: no cover
        raise ImportError("Panda3D not installed; cannot import hud_overlay") from e


def default_color_map() -> dict[str, Tuple[float, float, float, float]]:
    return {
        "ui": (0.22, 1.0, 0.25, 1.0),
        "friendly": (0.2, 0.7, 1.0, 1.0),
        "hostile": (1.0, 0.25, 0.25, 1.0),
        "warning": (1.0, 0.85, 0.2, 1.0),
        "neutral": (0.9, 0.9, 0.9, 1.0),
    }


class _DynamicLines2D:
    def __init__(self, parent: Any, max_segments: int = 256):
        self.max_segments = int(max_segments)
        fmt = GeomVertexFormat.get_v3c4()
        self.vdata = GeomVertexData("hud_lines", fmt, Geom.UHDynamic)
        self.vdata.set_num_rows(self.max_segments * 2)

        self._vw = GeomVertexWriter(self.vdata, "vertex")
        self._cw = GeomVertexWriter(self.vdata, "color")

        prim = GeomLines(Geom.UHDynamic)
        # Pre-allocate all indices
        for i in range(self.max_segments):
            prim.add_vertices(2 * i, 2 * i + 1)
        prim.close_primitive()

        geom = Geom(self.vdata)
        geom.add_primitive(prim)

        node = GeomNode("hud_lines")
        node.add_geom(geom)

        self.np = parent.attach_new_node(node)
        self.np.set_transparency(TransparencyAttrib.M_alpha)

    def update(
        self, segments: list[Tuple[Tuple[float, float], Tuple[float, float], Tuple[float, float, float, float]]]
    ):
        # Clamp
        n = min(len(segments), self.max_segments)
        self._vw.set_row(0)
        self._cw.set_row(0)
        for i in range(n):
            (a, b, rgba) = segments[i]
            self._vw.add_data3(a[0], 0.0, a[1])
            self._cw.add_data4(*rgba)
            self._vw.add_data3(b[0], 0.0, b[1])
            self._cw.add_data4(*rgba)

        # Hide remaining segments by collapsing them to 0-size with alpha 0
        for i in range(n, self.max_segments):
            self._vw.add_data3(0.0, 0.0, 0.0)
            self._cw.add_data4(0.0, 0.0, 0.0, 0.0)
            self._vw.add_data3(0.0, 0.0, 0.0)
            self._cw.add_data4(0.0, 0.0, 0.0, 0.0)


@dataclass
class P3DHudOverlay:
    parent_2d: Any
    color_map: Optional[dict[str, Tuple[float, float, float, float]]] = None
    max_segments: int = 256

    def __post_init__(self) -> None:
        if self.color_map is None:
            self.color_map = default_color_map()
        self._lines = _DynamicLines2D(self.parent_2d, max_segments=self.max_segments)
        self._texts: list[Any] = []

    def update(self, drawlist: HudDrawList) -> None:
        segments: list[Tuple[Tuple[float, float], Tuple[float, float], Tuple[float, float, float, float]]] = []
        # Convert primitives to line segments; circles approximated by polyline (cheap)
        for prim in drawlist:
            if isinstance(prim, HudLine):
                rgba = self._rgba(prim.color_key, prim.alpha)
                segments.append((prim.a, prim.b, rgba))
            elif isinstance(prim, HudBox):
                rgba = self._rgba(prim.color_key, prim.alpha)
                cx, cy = prim.center
                hx, hy = prim.half_extents
                corners = [
                    (cx - hx, cy - hy),
                    (cx + hx, cy - hy),
                    (cx + hx, cy + hy),
                    (cx - hx, cy + hy),
                ]
                for a, b in zip(corners, corners[1:] + corners[:1]):
                    segments.append((a, b, rgba))
            elif isinstance(prim, HudCircle):
                rgba = self._rgba(prim.color_key, prim.alpha)
                segments.extend(_circle_segments(prim.center, prim.radius, rgba, steps=24))

        self._lines.update(segments)

        # Text pool
        for t in self._texts:
            t.hide()

        text_i = 0
        for prim in drawlist:
            if not isinstance(prim, HudText):
                continue
            t = self._get_text(text_i)
            text_i += 1
            rgba = self._rgba(prim.color_key, prim.alpha)
            t.setText(prim.text)
            t.setPos(prim.pos[0], prim.pos[1])
            t.setFg(rgba)
            t.setScale(0.05 * (prim.size_px / 12.0))
            t.show()

    def _rgba(self, key: str, alpha: float) -> Tuple[float, float, float, float]:
        assert self.color_map is not None
        default_rgba = self.color_map.get("ui", (1.0, 1.0, 1.0, 1.0))
        r, g, b, a = self.color_map.get(key, default_rgba)
        return (r, g, b, float(a * alpha))

    def _get_text(self, idx: int) -> Any:
        while idx >= len(self._texts):
            t = OnscreenText(text="", pos=(0, 0), scale=0.05, fg=(1, 1, 1, 1), mayChange=True)
            t.reparentTo(self.parent_2d)
            self._texts.append(t)
        return self._texts[idx]


def _circle_segments(
    center: Tuple[float, float],
    radius: float,
    rgba: Tuple[float, float, float, float],
    steps: int = 24,
) -> list[Tuple[Tuple[float, float], Tuple[float, float], Tuple[float, float, float, float]]]:
    cx, cy = center
    out: list[Tuple[Tuple[float, float], Tuple[float, float], Tuple[float, float, float, float]]] = []
    for i in range(steps):
        a0 = 2 * np.pi * i / steps
        a1 = 2 * np.pi * (i + 1) / steps
        p0 = (cx + radius * np.cos(a0), cy + radius * np.sin(a0))
        p1 = (cx + radius * np.cos(a1), cy + radius * np.sin(a1))
        out.append((p0, p1, rgba))
    return out
