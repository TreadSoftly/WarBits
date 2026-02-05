"""HUD primitives + context types.

Design goals:
- Renderer-agnostic logic. Rendering backends convert primitives to artists/geometry.
- Deterministic outputs under deterministic inputs.
- Extremely light: the HUD should never be your FPS bottleneck.

Coordinate conventions:
- 2D HUD coordinates are NDC (normalized device coords): x,y in [-1,+1]
  where (0,0) is screen center.
- World coordinates are SI meters in right-handed coordinates.

"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Optional, Sequence, Tuple

import numpy as np
from numpy.typing import NDArray

NDC = Tuple[float, float]
Vec3 = NDArray[np.float_]


def _empty_str_dict() -> dict[str, str]:
    return {}


@dataclass(frozen=True)
class HudTheme:
    """Visual theme for HUD primitives.

    Keep it simple: colors are renderer-resolved; here we only carry semantic names.
    """

    # Semantic color keys. Renderers decide actual RGBA.
    friendly: str = "friendly"
    hostile: str = "hostile"
    neutral: str = "neutral"
    ui: str = "ui"
    warning: str = "warning"

    # Common style knobs
    line_width_px: float = 1.5
    glow: bool = False
    pixel_snap: int = 0  # 0 disables; otherwise snap to this many pixels per half-axis.


@dataclass(frozen=True)
class TargetTrack:
    """A minimal target track for HUD/targeting."""

    track_id: str
    position_m: Vec3
    velocity_mps: Vec3 = field(default_factory=lambda: np.zeros(3, dtype=float))
    classification: Literal["air", "ground", "missile", "unknown"] = "unknown"
    hostile: bool = True
    alive: bool = True


@dataclass(frozen=True)
class WeaponInfo:
    """Weapon parameters relevant to aiming symbology."""

    weapon_family: Literal["gun", "rocket", "missile", "bomb", "none"] = "none"
    muzzle_speed_mps: float = 0.0
    gravity_mps2: float = 9.80665
    drag_model: Literal["none", "simple"] = "none"  # HUD uses simple models only


@dataclass(frozen=True)
class CameraInfo:
    """Camera / projection info for mapping world points onto the HUD."""

    position_m: Vec3
    forward: Vec3
    up: Vec3
    fov_y_deg: float
    aspect: float  # width / height


@dataclass(frozen=True)
class HudContext:
    """All data needed to produce a HUD draw list."""

    time_s: float
    ownship_pos_m: Vec3
    ownship_vel_mps: Vec3
    ownship_heading_deg: float
    ownship_alt_m: float
    ownship_speed_mps: float
    camera: CameraInfo

    # What the pilot/AI is currently engaging.
    tracks: Sequence[TargetTrack] = field(default_factory=tuple)
    selected_track_id: Optional[str] = None

    weapon: WeaponInfo = field(default_factory=WeaponInfo)

    # Arbitrary extras (for debug text)
    debug: dict[str, str] = field(default_factory=_empty_str_dict)


# -------------------------
# HUD primitives
# -------------------------


@dataclass(frozen=True)
class HudLine:
    a: NDC
    b: NDC
    color_key: str = "ui"
    width_px: float = 1.5
    dashed: bool = False
    alpha: float = 1.0


@dataclass(frozen=True)
class HudCircle:
    center: NDC
    radius: float
    color_key: str = "ui"
    width_px: float = 1.2
    dashed: bool = False
    alpha: float = 1.0


@dataclass(frozen=True)
class HudBox:
    center: NDC
    half_extents: Tuple[float, float]
    color_key: str = "ui"
    width_px: float = 1.2
    alpha: float = 1.0


@dataclass(frozen=True)
class HudText:
    pos: NDC
    text: str
    color_key: str = "ui"
    size_px: float = 12.0
    align: Literal["left", "center", "right"] = "left"
    valign: Literal["bottom", "center", "top"] = "bottom"
    alpha: float = 1.0


HudPrimitive = HudLine | HudCircle | HudBox | HudText


@dataclass(frozen=True)
class HudDrawList:
    """A frame's HUD primitives."""

    primitives: Tuple[HudPrimitive, ...] = ()

    def __iter__(self):
        return iter(self.primitives)

    def __len__(self):
        return len(self.primitives)
