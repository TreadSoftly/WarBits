from __future__ import annotations

from typing import Any


def apply_neon_style(fig: Any, ax: Any) -> None:
    """Apply a WarBits 'holo wireframe' look to a Matplotlib 3D axis."""
    fig.patch.set_facecolor("black")
    ax.set_facecolor("black")
    # Remove axes decorations to look like a sim overlay.
    ax.set_axis_off()
    ax.set_axis_off()
    ax.set_axis_off()
