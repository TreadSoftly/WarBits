from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class WireframeP3DStyle:
    """Style settings for Panda3D wireframe rendering.

    Note: line thickness is driver-dependent for GeomLines.
    If you need 'guaranteed thick lines', the later pack will add
    a shader-based approach (lines as camera-facing quads).
    """

    # RGBA in [0,1]
    color: Tuple[float, float, float, float] = (0.2, 1.0, 0.2, 1.0)

    # 1.0 is safest across GPUs; > 1 may be clamped.
    line_thickness: float = 1.0

    # Additive blend gives that neon vibe, but can wash out with many lines.
    additive_blend: bool = True

    # If True, disable lighting on the wireframe geometry.
    unlit: bool = True

    # If True, render on top (debug mode). For real gameplay you'd typically keep depth.
    overlay: bool = False


NEON_GREEN = WireframeP3DStyle(color=(0.2, 1.0, 0.2, 1.0), line_thickness=1.0, additive_blend=True, unlit=True)
