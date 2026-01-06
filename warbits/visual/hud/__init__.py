"""HUD subsystem.

Entry points:
- HudBuilder: produces a HudDrawList from a HudContext.
- Projectors: map world points to NDC.
- MplHudOverlay / P3DHudOverlay: render the draw list.

"""

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
from .projector import PinholeProjector, ScreenProjector
from .targeting import LeadSolution, lead_solution_simple, solve_intercept_no_gravity
from .builder import HudBuilder
