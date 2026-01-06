from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

@dataclass(frozen=True)
class GlowStyle:
    """Multi-pass glow parameters (renderer may approximate)."""
    passes: int = 3
    outer_alpha: float = 0.08
    outer_width_mul: float = 3.0

@dataclass(frozen=True)
class WireframeStyle:
    """Renderer-agnostic wireframe styling hints."""

    color: str = "#39FF14"
    alpha: float = 1.0

    # Primary silhouette lines
    silhouette_width: float = 1.8
    silhouette_dash: Optional[Tuple[float, float]] = None

    # Secondary internal structure lines
    rib_width: float = 0.9
    rib_dash: Optional[Tuple[float, float]] = (2.0, 3.0)
    rib_alpha: float = 0.85

    glow: Optional[GlowStyle] = GlowStyle()
