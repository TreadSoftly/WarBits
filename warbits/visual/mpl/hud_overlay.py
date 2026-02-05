"""Matplotlib 2D HUD overlay renderer.

The goal is to render HUD primitives with:
- minimal allocations per frame
- re-used Artists
- renderer-agnostic primitive list

This module does NOT depend on your sim core.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple, cast

try:
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    from matplotlib.patches import Circle
except Exception:  # pragma: no cover
    plt = None
    Line2D = None
    Circle = None

from ..hud.types import HudBox, HudCircle, HudDrawList, HudLine

RGBA = Tuple[float, float, float, float]


def default_color_map() -> Dict[str, Tuple[float, float, float, float]]:
    # Neon-ish defaults
    return {
        "ui": (0.22, 1.0, 0.25, 1.0),
        "friendly": (0.2, 0.7, 1.0, 1.0),
        "hostile": (1.0, 0.25, 0.25, 1.0),
        "warning": (1.0, 0.85, 0.2, 1.0),
        "neutral": (0.9, 0.9, 0.9, 1.0),
    }


@dataclass
class MplHudOverlay:
    fig: Any
    zorder: int = 50
    color_map: Optional[Dict[str, RGBA]] = None

    def __post_init__(self):
        if plt is None:
            raise RuntimeError("Matplotlib not available; cannot use MplHudOverlay")
        if Line2D is None or Circle is None:
            raise RuntimeError("Matplotlib artists not available; cannot use MplHudOverlay")
        if self.color_map is None:
            self.color_map = default_color_map()

        self._Line2D = cast(Any, Line2D)
        self._Circle = cast(Any, Circle)

        # Create a full-figure overlay axis in NDC [-1,+1]
        self.ax = self.fig.add_axes([0.0, 0.0, 1.0, 1.0], frameon=False)
        self.ax.set_xlim(-1, 1)
        self.ax.set_ylim(-1, 1)
        self.ax.set_axis_off()
        self.ax.set_zorder(self.zorder)

        # Pools
        self._lines: List[Any] = []
        self._circles: List[Any] = []
        self._texts: List[Any] = []

    def update(self, drawlist: HudDrawList):
        """Update artists to match drawlist."""
        # Mark all hidden first
        for ln in self._lines:
            ln.set_visible(False)
        for c in self._circles:
            c.set_visible(False)
        for t in self._texts:
            t.set_visible(False)

        line_i = circ_i = text_i = 0

        for prim in drawlist.primitives:
            if isinstance(prim, HudLine):
                ln = self._get_line(line_i)
                line_i += 1
                rgba = self._rgba(prim.color_key)
                ln.set_data([prim.a[0], prim.b[0]], [prim.a[1], prim.b[1]])
                ln.set_color(rgba)
                ln.set_alpha(prim.alpha)
                ln.set_linewidth(prim.width_px)
                ln.set_linestyle("--" if prim.dashed else "-")
                ln.set_visible(True)
            elif isinstance(prim, HudCircle):
                c = self._get_circle(circ_i)
                circ_i += 1
                rgba = self._rgba(prim.color_key)
                c.center = prim.center
                c.radius = prim.radius
                c.set_edgecolor(rgba)
                c.set_alpha(prim.alpha)
                c.set_linewidth(prim.width_px)
                c.set_fill(False)
                c.set_linestyle("--" if prim.dashed else "-")
                c.set_visible(True)
            elif isinstance(prim, HudBox):
                # 4 lines
                cx, cy = prim.center
                hx, hy = prim.half_extents
                rgba = self._rgba(prim.color_key)
                corners = [
                    (cx - hx, cy - hy),
                    (cx + hx, cy - hy),
                    (cx + hx, cy + hy),
                    (cx - hx, cy + hy),
                ]
                segs = list(zip(corners, corners[1:] + corners[:1]))
                for a, b in segs:
                    ln = self._get_line(line_i)
                    line_i += 1
                    ln.set_data([a[0], b[0]], [a[1], b[1]])
                    ln.set_color(rgba)
                    ln.set_alpha(prim.alpha)
                    ln.set_linewidth(prim.width_px)
                    ln.set_linestyle("-")
                    ln.set_visible(True)
            else:
                text_prim = prim
                t = self._get_text(text_i)
                text_i += 1
                rgba = self._rgba(text_prim.color_key)
                t.set_position(text_prim.pos)
                t.set_text(text_prim.text)
                t.set_color(rgba)
                t.set_alpha(text_prim.alpha)
                t.set_fontsize(text_prim.size_px)
                t.set_horizontalalignment(text_prim.align)
                t.set_verticalalignment(text_prim.valign)
                t.set_visible(True)

        # Return artists for optional blitting
        return self.artists

    @property
    def artists(self) -> List[Any]:
        return [*self._lines, *self._circles, *self._texts]

    def _rgba(self, key: str) -> RGBA:
        if self.color_map is None:
            self.color_map = default_color_map()
        fallback = self.color_map.get("ui", (0.22, 1.0, 0.25, 1.0))
        return self.color_map.get(key, fallback)

    def _get_line(self, idx: int) -> Any:
        while idx >= len(self._lines):
            ln = self._Line2D([0, 0], [0, 0])
            ln.set_zorder(self.zorder)
            self.ax.add_line(ln)
            self._lines.append(ln)
        return self._lines[idx]

    def _get_circle(self, idx: int) -> Any:
        while idx >= len(self._circles):
            c = self._Circle((0, 0), radius=0.1, fill=False)
            c.set_zorder(self.zorder)
            self.ax.add_patch(c)
            self._circles.append(c)
        return self._circles[idx]

    def _get_text(self, idx: int) -> Any:
        while idx >= len(self._texts):
            t = self.ax.text(0, 0, "", transform=self.ax.transData)
            t.set_zorder(self.zorder)
            self._texts.append(t)
        return self._texts[idx]
