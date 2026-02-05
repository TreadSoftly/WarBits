"""HUD subsystem.

Entry points:
- HudBuilder: produces a HudDrawList from a HudContext.
- Projectors: map world points to NDC.
- MplHudOverlay / P3DHudOverlay: render the draw list.

"""

from .builder import HudBuilder
from .projector import PinholeProjector, ScreenProjector
from .targeting import LeadSolution, lead_solution_simple, solve_intercept_no_gravity
from .types import (
    CameraInfo,
    HudBox,
    HudCircle,
    HudContext,
    HudDrawList,
    HudLine,
    HudText,
    HudTheme,
    TargetTrack,
    WeaponInfo,
)

__all__ = [
    "CameraInfo",
    "HudBox",
    "HudCircle",
    "HudContext",
    "HudDrawList",
    "HudLine",
    "HudText",
    "HudTheme",
    "TargetTrack",
    "WeaponInfo",
    "PinholeProjector",
    "ScreenProjector",
    "LeadSolution",
    "lead_solution_simple",
    "solve_intercept_no_gravity",
    "HudBuilder",
]
