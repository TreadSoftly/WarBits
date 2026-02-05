"""warbits.visual.panda3d.hud

Minimal HUD primitives for the WarBits wireframe aesthetic in Panda3D.

This is not a 'full UI system' — it's a low-allocation overlay that:
- renders crisp neon-green text
- renders a simple reticle (crosshair)
- can be updated every frame without creating new objects

Safe to import without Panda3D installed.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional, Tuple, cast

from .imports import require_panda3d

RGBA = Tuple[float, float, float, float]


@dataclass(frozen=True)
class HudStyle:
    text_rgba: RGBA = (0.20, 1.00, 0.20, 1.0)
    text_scale: float = 0.045
    margin: float = 0.04
    reticle_size: float = 0.03
    reticle_thickness: float = 2.0


def _fmt(name: str, value: float, unit: str = "") -> str:
    if unit:
        return f"{name}: {value:,.1f} {unit}"
    return f"{name}: {value:,.1f}"


class BasicHUD:
    """A lightweight HUD: left block, right block, center reticle."""

    def __init__(self, base: Any, style: HudStyle = HudStyle()):
        self.base = base
        self.style = style

        require_panda3d()
        from direct.gui.OnscreenText import OnscreenText  # type: ignore
        from panda3d.core import TextNode  # type: ignore

        OnscreenTextAny = cast(Any, OnscreenText)
        TextNodeAny = cast(Any, TextNode)

        self._OnscreenText = OnscreenTextAny
        self._TextNode = TextNodeAny

        # Left info block (top-left)
        self.left = OnscreenTextAny(
            text="",
            pos=(-1.0 + style.margin, 1.0 - style.margin),
            scale=style.text_scale,
            fg=style.text_rgba,
            align=TextNodeAny.ALeft,
            mayChange=True,
        )
        self.left.setBin("fixed", 50)
        self.left.setDepthTest(False)
        self.left.setDepthWrite(False)

        # Right info block (top-right)
        self.right = OnscreenTextAny(
            text="",
            pos=(1.0 - style.margin, 1.0 - style.margin),
            scale=style.text_scale,
            fg=style.text_rgba,
            align=TextNodeAny.ARight,
            mayChange=True,
        )
        self.right.setBin("fixed", 50)
        self.right.setDepthTest(False)
        self.right.setDepthWrite(False)

        # Center reticle: simple crosshair built from LineSegs
        self.reticle_np = self._build_reticle()

        self._left_cache: str = ""
        self._right_cache: str = ""

    def _build_reticle(self) -> Any:
        require_panda3d()
        from panda3d.core import LineSegs, NodePath  # type: ignore

        LineSegs = cast(Any, LineSegs)
        NodePath = cast(Any, NodePath)

        s = float(self.style.reticle_size)
        ls = LineSegs()
        ls.setThickness(float(self.style.reticle_thickness))
        ls.setColor(*self.style.text_rgba)

        # Horizontal line
        ls.moveTo(-s, 0.0, 0.0)
        ls.drawTo(s, 0.0, 0.0)

        # Vertical line
        ls.moveTo(0.0, -s, 0.0)
        ls.drawTo(0.0, s, 0.0)

        np_node = NodePath(ls.create())
        np_node.reparentTo(self.base.aspect2d)
        np_node.setBin("fixed", 60)
        np_node.setDepthTest(False)
        np_node.setDepthWrite(False)
        return np_node

    def set_left_text(self, text: str) -> None:
        if text != self._left_cache:
            self.left.setText(text)
            self._left_cache = text

    def set_right_text(self, text: str) -> None:
        if text != self._right_cache:
            self.right.setText(text)
            self._right_cache = text

    def update_basic(
        self,
        *,
        speed_mps: float,
        altitude_m: float,
        heading_deg: float,
        fps: Optional[float] = None,
    ) -> None:
        # Left block: flight-ish.
        left = "\n".join(
            [
                _fmt("SPD", speed_mps, "m/s"),
                _fmt("ALT", altitude_m, "m"),
                _fmt("HDG", heading_deg, "deg"),
            ]
        )

        # Right block: FPS + misc.
        right_lines: list[str] = []
        if fps is not None:
            right_lines.append(_fmt("FPS", fps, ""))

        right = "\n".join(right_lines) if right_lines else ""

        self.set_left_text(left)
        self.set_right_text(right)

    def destroy(self) -> None:
        # OnscreenText is a NodePath-like object
        self.left.destroy()
        self.right.destroy()
        self.reticle_np.removeNode()
