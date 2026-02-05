from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Tuple

RGBA = Tuple[float, float, float, float]


def _rgba(hex_or_rgb: str | Tuple[float, float, float], alpha: float = 1.0) -> RGBA:
    """Convert a hex string like '#39FF14' or RGB tuple to RGBA tuple."""
    if isinstance(hex_or_rgb, str):
        s = hex_or_rgb.strip()
        if s.startswith("#") and len(s) in (7, 9):
            r = int(s[1:3], 16) / 255.0
            g = int(s[3:5], 16) / 255.0
            b = int(s[5:7], 16) / 255.0
            return (r, g, b, float(alpha))
        raise ValueError(f"Unsupported color string: {hex_or_rgb!r}")
    r, g, b = hex_or_rgb
    return (float(r), float(g), float(b), float(alpha))


@dataclass(frozen=True)
class WireframePalette:
    """Semantic color palette for the sim.

    A renderer should pick colors based on 'roles', not on hard-coded hex strings.
    """

    friendly: RGBA
    hostile: RGBA
    neutral: RGBA
    terrain: RGBA
    projectile: RGBA
    ui: RGBA
    warning: RGBA
    dim: RGBA

    def color_for_role(self, role: str) -> RGBA:
        role = (role or "neutral").lower()
        if role in ("friendly", "player", "ally"):
            return self.friendly
        if role in ("hostile", "enemy", "bogie"):
            return self.hostile
        if role in ("neutral",):
            return self.neutral
        if role in ("terrain", "ground"):
            return self.terrain
        if role in ("projectile", "bullet", "rocket", "bomb", "missile"):
            return self.projectile
        if role in ("ui", "hud"):
            return self.ui
        if role in ("warn", "warning"):
            return self.warning
        if role in ("dim", "shadow"):
            return self.dim
        # fallback: neutral
        return self.neutral


@dataclass(frozen=True)
class WireframeStyle:
    """Rendering style for wireframe blueprints in Matplotlib.

    The 'outline' pass draws the primary silhouette edges.
    The 'detail' pass draws optional internal structure edges (ribs/panels).

    Glow is implemented as an additional 'outline glow' pass: same segments,
    larger linewidth, lower alpha.
    """

    palette: WireframePalette

    outline_lw: float = 1.8
    outline_alpha: float = 1.0

    detail_lw: float = 1.0
    detail_alpha: float = 0.55

    # Optional glow
    glow_enabled: bool = True
    glow_lw_multiplier: float = 2.6
    glow_alpha_multiplier: float = 0.18

    # Distance fading (helps readability + perf when lots of units exist).
    # Alpha is scaled by: fade = 1 / (1 + (dist / fade_distance)**2)
    fade_distance_m: float = 3500.0

    # When using "pixel" aesthetics, some teams prefer slightly chunkier lines.
    pixel_outline_lw_multiplier: float = 1.2
    pixel_detail_lw_multiplier: float = 1.0

    def alpha_fade(self, distance_m: float) -> float:
        d = max(0.0, float(distance_m))
        fd = float(self.fade_distance_m)
        if fd <= 1e-6:
            return 1.0
        return 1.0 / (1.0 + (d / fd) ** 2)

    def resolve_pass(
        self, role: str, distance_m: float, *, pixel_mode: bool, detail: bool
    ) -> Tuple[RGBA, float, float, bool]:
        """Return (rgba, lw, alpha, glow) for a pass."""
        base_rgba = self.palette.color_for_role(role)
        fade = self.alpha_fade(distance_m)

        if detail:
            lw = self.detail_lw * (self.pixel_detail_lw_multiplier if pixel_mode else 1.0)
            alpha = self.detail_alpha * fade
            return (base_rgba[0], base_rgba[1], base_rgba[2], alpha), lw, alpha, False

        lw = self.outline_lw * (self.pixel_outline_lw_multiplier if pixel_mode else 1.0)
        alpha = self.outline_alpha * fade
        return (base_rgba[0], base_rgba[1], base_rgba[2], alpha), lw, alpha, True


def neon_green_style(*, friendly_only: bool = False) -> WireframeStyle:
    """Default WarBits 'holographic green' look."""
    green = _rgba("#39FF14", 1.0)
    red = _rgba("#FF3B30", 1.0)
    cyan = _rgba("#00E5FF", 1.0)
    terrain = _rgba("#1B5E20", 0.35)  # dim green for terrain wire
    projectile = _rgba("#FFD60A", 1.0)  # warm tracer
    ui = _rgba("#39FF14", 1.0)
    warning = _rgba("#FF9F0A", 1.0)
    dim = _rgba("#39FF14", 0.25)

    if friendly_only:
        red = green
        cyan = green

    pal = WireframePalette(
        friendly=green,
        hostile=red,
        neutral=cyan,
        terrain=terrain,
        projectile=projectile,
        ui=ui,
        warning=warning,
        dim=dim,
    )
    return WireframeStyle(palette=pal)


def thermal_style() -> WireframeStyle:
    """A 'thermal camera' inspired palette (still wireframe).

    This is NOT a real thermal model; it's a visualization mode.
    """
    hot = _rgba("#FF9F0A", 1.0)
    hostile = _rgba("#FF3B30", 1.0)
    neutral = _rgba("#C7C7CC", 1.0)
    terrain = _rgba("#2C2C2E", 0.55)
    projectile = _rgba("#FFD60A", 1.0)
    ui = _rgba("#FFFFFF", 0.95)
    warning = _rgba("#FF3B30", 1.0)
    dim = _rgba("#FFFFFF", 0.2)

    pal = WireframePalette(
        friendly=hot,
        hostile=hostile,
        neutral=neutral,
        terrain=terrain,
        projectile=projectile,
        ui=ui,
        warning=warning,
        dim=dim,
    )
    return WireframeStyle(palette=pal, outline_lw=2.0, detail_alpha=0.4, glow_enabled=False)


def apply_mpl_dark_theme(fig: Any, ax: Any) -> None:
    """Apply a consistent dark theme to a Matplotlib figure+3D axis."""
    fig.patch.set_facecolor("black")
    ax.set_facecolor("black")
    # Hide axes chrome for a 'sim overlay' look.
    try:
        ax.set_axis_off()
    except Exception:
        # Some Matplotlib versions backends are finicky; be tolerant.
        pass
    # Avoid autoscale cost.
    ax.grid(False)
    # Make panes dark and subtle.
    for axis in (ax.xaxis, ax.yaxis, ax.zaxis):
        try:
            axis.pane.set_facecolor((0.0, 0.0, 0.0, 0.0))
            axis.pane.set_edgecolor((0.0, 0.0, 0.0, 0.0))
        except Exception:
            pass
    # Ticks off
    try:
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_zticks([])
    except Exception:
        pass
