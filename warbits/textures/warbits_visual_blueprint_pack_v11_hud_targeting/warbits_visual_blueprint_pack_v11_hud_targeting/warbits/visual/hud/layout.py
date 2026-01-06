"""HUD layout helpers.

We keep layout in NDC coordinates [-1,+1].
This means it's renderer-agnostic:
- Matplotlib overlay axis uses the same space.
- Panda3D aspect2d uses a similar centered coordinate system.

"""

from __future__ import annotations

from dataclasses import dataclass

from .types import NDC


@dataclass(frozen=True)
class HudLayout:
    # Common anchor points
    speed_pos: NDC = (-0.98, -0.92)
    alt_pos: NDC = (-0.98, -0.98)
    heading_pos: NDC = (0.0, 0.92)

    target_label_offset: NDC = (0.02, 0.02)

    # Crosshair sizing
    crosshair_half: float = 0.04
    crosshair_gap: float = 0.01

    # Target box
    target_box_half: float = 0.05

    # Lead circle
    lead_radius: float = 0.035

    # Horizon line
    horizon_half_width: float = 0.55
    horizon_thickness_px: float = 1.2


DEFAULT_LAYOUT = HudLayout()
