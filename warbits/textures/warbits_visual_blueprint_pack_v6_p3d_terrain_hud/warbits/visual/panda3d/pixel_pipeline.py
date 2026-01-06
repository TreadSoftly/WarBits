from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

from .imports import require_panda3d


@dataclass
class PixelateConfig:
    width: int = 640
    height: int = 360
    # Nearest-neighbor sampling gives the pixel vibe.
    nearest: bool = True


class PixelatePipeline:
    """Very small 'pixelate' pipeline for Panda3D.

    This is intentionally minimal in v5. It renders the 3D scene to a low-res
    offscreen buffer, then displays that texture full-screen.

    Later packs can add:
    - bloom/glow for the neon lines
    - CRT distortion, scanlines, etc.

    Usage:
        p3d, ShowBase = require_panda3d()
        base = ShowBase()
        pipeline = PixelatePipeline(base, PixelateConfig(640, 360))
        pipeline.enable()

    """

    def __init__(self, base, config: PixelateConfig):
        self._p3d, _ = require_panda3d()
        self.base = base
        self.config = config

        self.buffer = None
        self.tex = None
        self.card_np = None
        self.cam_np = None

    def enable(self) -> None:
        p3d = self._p3d

        tex = p3d.Texture()
        if self.config.nearest:
            tex.setMinfilter(p3d.SamplerState.FTNearest)
            tex.setMagfilter(p3d.SamplerState.FTNearest)

        # Create an offscreen buffer to render the 3D scene.
        buffer = self.base.win.makeTextureBuffer(
            "pixelate_buffer",
            self.config.width,
            self.config.height,
            tex,
        )
        buffer.setClearColor(self.base.win.getClearColor())

        # Create a camera that renders the main scene into the offscreen buffer.
        cam = self.base.makeCamera(buffer)
        cam.reparentTo(self.base.camera)
        cam.node().setLens(self.base.cam.node().getLens())

        # Disable the default camera so only the pixelated output is visible.
        self.base.cam.node().setActive(False)

        # Display the low-res texture on a full-screen card in render2d.
        cm = p3d.CardMaker("pixelate_card")
        cm.setFrameFullscreenQuad()
        card = p3d.NodePath(cm.generate())
        card.reparentTo(self.base.render2d)
        card.setTexture(tex)

        self.buffer = buffer
        self.tex = tex
        self.card_np = card
        self.cam_np = cam

    def disable(self) -> None:
        if self.card_np is not None:
            self.card_np.removeNode()
            self.card_np = None
        if self.cam_np is not None:
            self.cam_np.removeNode()
            self.cam_np = None
        if self.buffer is not None:
            self.base.graphicsEngine.removeWindow(self.buffer)
            self.buffer = None
        self.tex = None
        # Re-enable default camera
        self.base.cam.node().setActive(True)

