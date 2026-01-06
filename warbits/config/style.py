# pyright: reportMissingTypeStubs=false, reportUnknownMemberType=false
# ── warbits/config/style.py ────────────────────────────────────────────────
from __future__ import annotations

from cycler import cycler
from typing import TYPE_CHECKING, Any, cast

import matplotlib.style as _mplstyle

# ── typing-only heavy imports (silenced if stubs are missing) ──────────────
if TYPE_CHECKING:
    from matplotlib.figure import Figure                     # std stub exists
    from mpl_toolkits.mplot3d import Axes3D                  # type: ignore[import-not-found]
else:                                                        # very light fall-backs
    Figure = Any      # type: ignore[assignment]
    Axes3D = Any      # type: ignore[assignment]

try:
    import matplotlib as mpl                                 # type: ignore
except Exception:                                            # headless / stub-less
    mpl = None                                               # type: ignore

# ─────────────────────────── 1 · dark theme ───────────────────────────────
def apply_style() -> None:                                   # noqa: C901
    """Apply WarBits dark palette (idempotent, safe in headless mode)."""
    if mpl is None:
        return

    _mplstyle.use("fast")

    rc = mpl.rcParams
    rc.update({
        # colours & globals
        "figure.facecolor": "black",
        "axes.facecolor":   "black",
        "axes.edgecolor":   (0.05, 0.05, 0.1),
        "axes.linewidth":   1,
        "grid.color":       "none",
        "axes.grid":        False,
        "figure.dpi":       40,
        "savefig.facecolor": "black",
        "savefig.edgecolor": "black",
        "savefig.transparent": True,
        # typography
        "font.family": "sans-serif",
        "font.size":   10,
        "axes.labelsize": 10,
        "axes.titlesize": 10,
        "axes.titleweight": "bold",
        "axes.titlecolor":  "#FF0000",
        "legend.fontsize":  8,
        "legend.frameon":   True,
        "legend.fancybox":  True,
        "legend.framealpha": 1,
        "legend.edgecolor": "none",
        # ticks / spines
        "xtick.color": "none",
        "ytick.color": "none",
        "xtick.major.size": 10,
        "xtick.minor.size": 3,
        "xtick.direction":  "in",
        "ytick.left": True,
        "axes.spines.top":   True,
        "axes.spines.right": True,
        "axes.spines.left":  True,
        "axes.spines.bottom": False,
        "axes.xmargin": 0.02,
        "axes.ymargin": 0.02,
        "axes.axisbelow": True,
        # cycles & line defaults
        "axes.prop_cycle": cycler(color=[
            "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
            "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf"]),
        "lines.linewidth": 1.0,
        "lines.markersize": 5,
        "lines.markeredgewidth": 1.3,
        # toolbar
        "toolbar": "None",
    })


# ─────────────────────────── 2 · window helpers ───────────────────────────
def make_fullscreen(fig: Figure) -> None:
    """Attempt fullscreen; fall back to maximise (cross-backend)."""
    if mpl is None:
        return

    mng      = fig.canvas.manager                     # type: ignore[attr-defined]
    backend  = mpl.get_backend().lower()
    try:
        fig.patch.set_facecolor("black")
    except Exception:
        pass

    try:                                             # preferred fullscreen
        if "tkagg" in backend:
            mng.window.attributes("-fullscreen", True)      # type: ignore[attr-defined]
        elif "qt" in backend:
            mng.window.showFullScreen()                     # type: ignore[attr-defined]
        elif "wx" in backend:
            mng.frame.ShowFullScreen(True)                  # type: ignore[attr-defined]
    except Exception:                                      # graceful maximise
        try:
            if "tkagg" in backend:
                mng.window.state("zoomed")                  # type: ignore[attr-defined]
            elif "qt" in backend:
                mng.window.showMaximized()                  # type: ignore[attr-defined]
            elif "wx" in backend:
                mng.frame.Maximize(True)                    # type: ignore[attr-defined]
        except Exception:
            pass

    if fig.canvas.manager is not None:
        fig.canvas.manager.set_window_title("")
    try:
        if "qt" in backend:
            mng.window.setStyleSheet("background-color: black;")  # type: ignore[attr-defined]
            mng.window.setContentsMargins(0, 0, 0, 0)             # type: ignore[attr-defined]
            layout: Any = cast(Any, mng.window.layout())          # type: ignore[attr-defined]
            if layout is not None:
                layout.setContentsMargins(0, 0, 0, 0)
                layout.setSpacing(0)
            central = cast(Any, mng.window.centralWidget())       # type: ignore[attr-defined]
            if central is not None:
                central.setContentsMargins(0, 0, 0, 0)
                central.setStyleSheet("background-color: black;")
                central_layout: Any = None
                layout_fn: Any = getattr(central, "layout", None)
                if callable(layout_fn):
                    try:
                        central_layout = cast(Any, layout_fn())
                    except Exception:
                        central_layout = None
                if central_layout is not None:
                    central_layout.setContentsMargins(0, 0, 0, 0)
                    central_layout.setSpacing(0)
            try:
                fig.canvas.setStyleSheet("background-color: black;")  # type: ignore[attr-defined]
            except Exception:
                pass
    except Exception:
        pass

    try:
        if "tkagg" in backend:
            mng.window.configure(background="black")             # type: ignore[attr-defined]
            fig.patch.set_facecolor("black")
            fig.canvas.get_tk_widget().configure(                # type: ignore[attr-defined]
                background="black",
                highlightthickness=0,
                borderwidth=0,
            )
    except Exception:
        pass

def configure_3d_axes(
    ax: Axes3D,
    *,
    xlim: tuple[float, float] | None = None,
    ylim: tuple[float, float] | None = None,
    zlim: tuple[float, float] | None = None,
    elev: float = 30,
    azim: float = -45,
) -> None:
    """Apply WarBits camera limits & cosmetics to *ax*."""
    if xlim is None:
        xlim = (0.0, 18_500.0)
    if ylim is None:
        ylim = (4_000.0, 9_300.0)
    if zlim is None:
        zlim = (0.0, 15_000.0)
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.set_zlim(*zlim)
    if hasattr(ax, "set_box_aspect"):
        span_x = abs(xlim[1] - xlim[0])
        span_y = abs(ylim[1] - ylim[0])
        span_z = abs(zlim[1] - zlim[0])
        try:
            ax.set_box_aspect((max(span_x, 1.0), max(span_y, 1.0), max(span_z, 1.0)))
        except Exception:
            pass
    ax.view_init(elev=elev, azim=azim)
    ax.set_axis_off()

    for pane in (ax.xaxis.pane, ax.yaxis.pane, ax.zaxis.pane):   # type: ignore[attr-defined]
        pane.set_facecolor((0, 0, 0, 0))
        pane.set_edgecolor((0, 0, 0, 0))

__all__ = ["apply_style", "make_fullscreen", "configure_3d_axes"]
