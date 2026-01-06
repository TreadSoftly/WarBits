from __future__ import annotations

from dataclasses import dataclass
import random
from typing import Any, Literal, TYPE_CHECKING, cast, overload

import numpy as np
import numpy.typing as npt
if TYPE_CHECKING:
    from mpl_toolkits.mplot3d import Axes3D  # type: ignore
else:
    Axes3D = Any  # type: ignore[assignment]

from ..config import settings as _cfg
__all__ = [
    "TerrainProfile",
    "TERRAIN_PROFILES",
    "generate_terrain",
    "draw_terrain",
    "set_active_terrain",
    "sample_height",
]

_F64Arr = npt.NDArray[np.float64]
_PlotKw = dict[str, Any]

# --------------------------------------------------------------------------- #
# Active terrain sampling
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class TerrainGrid:
    x_min: float
    x_max: float
    y_min: float
    y_max: float
    dx: float
    dy: float
    z: _F64Arr
    nx: int
    ny: int


_active_terrain: TerrainGrid | None = None
_last_color_key: tuple[str, int] | None = None
_last_color_range: tuple[float, float] | None = None


def set_active_terrain(x_grid: _F64Arr, y_grid: _F64Arr, z_grid: _F64Arr) -> None:
    """Cache the latest terrain grid for fast height sampling."""
    global _active_terrain
    if x_grid.size == 0 or y_grid.size == 0 or z_grid.size == 0:
        _active_terrain = None
        return
    if x_grid.shape != y_grid.shape or x_grid.shape != z_grid.shape:
        _active_terrain = None
        return
    ny, nx = z_grid.shape
    if nx < 2 or ny < 2:
        _active_terrain = None
        return
    x_min = float(x_grid[0, 0])
    x_max = float(x_grid[0, -1])
    y_min = float(y_grid[0, 0])
    y_max = float(y_grid[-1, 0])
    dx = (x_max - x_min) / max(nx - 1, 1)
    dy = (y_max - y_min) / max(ny - 1, 1)
    if abs(dx) < 1e-9 or abs(dy) < 1e-9:
        _active_terrain = None
        return
    _active_terrain = TerrainGrid(
        x_min=x_min,
        x_max=x_max,
        y_min=y_min,
        y_max=y_max,
        dx=dx,
        dy=dy,
        z=z_grid,
        nx=nx,
        ny=ny,
    )


def sample_height(
    x: float | npt.NDArray[np.floating[Any]],
    y: float | npt.NDArray[np.floating[Any]],
    *,
    default: float = 0.0,
    clamp: bool = True,
) -> float | _F64Arr:
    """Return terrain height at (x, y) via bilinear interpolation."""
    grid = _active_terrain
    if grid is None:
        x_arr = np.asarray(x)
        y_arr = np.asarray(y)
        if x_arr.shape == () and y_arr.shape == ():
            return float(default)
        shape = np.broadcast(x_arr, y_arr).shape
        return np.full(shape, float(default), dtype=np.float64)

    x_arr = np.asarray(x, dtype=np.float64)
    y_arr = np.asarray(y, dtype=np.float64)
    x_arr, y_arr = np.broadcast_arrays(x_arr, y_arr)

    invalid = ~(np.isfinite(x_arr) & np.isfinite(y_arr))
    if invalid.shape == () and bool(invalid):
        return float(default)
    if np.any(invalid):
        x_safe = x_arr.copy()
        y_safe = y_arr.copy()
        x_safe[invalid] = grid.x_min
        y_safe[invalid] = grid.y_min
    else:
        x_safe = x_arr
        y_safe = y_arr

    ix = (x_safe - grid.x_min) / grid.dx
    iy = (y_safe - grid.y_min) / grid.dy
    if clamp:
        ix = np.clip(ix, 0.0, grid.nx - 1.0)
        iy = np.clip(iy, 0.0, grid.ny - 1.0)

    i0 = np.floor(ix).astype(np.int64)
    j0 = np.floor(iy).astype(np.int64)
    i1 = np.clip(i0 + 1, 0, grid.nx - 1)
    j1 = np.clip(j0 + 1, 0, grid.ny - 1)

    tx = ix - i0
    ty = iy - j0

    z00 = grid.z[j0, i0]
    z10 = grid.z[j0, i1]
    z01 = grid.z[j1, i0]
    z11 = grid.z[j1, i1]

    z0 = z00 + (z10 - z00) * tx
    z1 = z01 + (z11 - z01) * tx
    z = z0 + (z1 - z0) * ty

    if np.any(invalid):
        z = np.where(invalid, float(default), z)
    if z.ndim == 0:
        return float(z)
    return z

# --------------------------------------------------------------------------- #
# Terrain profiles
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class TerrainProfile:
    name: str
    amplitude: float
    base_freq: float
    base_weight: float
    ridge_freq: float
    ridge_weight: float
    grid_freq: float
    grid_weight: float
    noise_weight: float
    base_height: float
    cmap: str
    alpha: float | None = None
    edgecolor: str | None = None


TERRAIN_PROFILES: dict[str, TerrainProfile] = {
    "rolling": TerrainProfile(
        name="rolling",
        amplitude=600.0,
        base_freq=1500.0,
        base_weight=0.4,
        ridge_freq=1800.0,
        ridge_weight=0.15,
        grid_freq=1000.0,
        grid_weight=0.0,
        noise_weight=0.25,
        base_height=0.0,
        cmap="terrain",
    ),
    "desert": TerrainProfile(
        name="desert",
        amplitude=320.0,
        base_freq=2400.0,
        base_weight=0.35,
        ridge_freq=2600.0,
        ridge_weight=0.08,
        grid_freq=1200.0,
        grid_weight=0.0,
        noise_weight=0.18,
        base_height=0.0,
        cmap="YlOrBr",
    ),
    "mountain": TerrainProfile(
        name="mountain",
        amplitude=1400.0,
        base_freq=900.0,
        base_weight=0.45,
        ridge_freq=650.0,
        ridge_weight=0.6,
        grid_freq=900.0,
        grid_weight=0.0,
        noise_weight=0.28,
        base_height=120.0,
        cmap="gist_earth",
    ),
    "forest": TerrainProfile(
        name="forest",
        amplitude=500.0,
        base_freq=1700.0,
        base_weight=0.4,
        ridge_freq=1400.0,
        ridge_weight=0.25,
        grid_freq=900.0,
        grid_weight=0.0,
        noise_weight=0.32,
        base_height=40.0,
        cmap="Greens",
    ),
    "urban": TerrainProfile(
        name="urban",
        amplitude=140.0,
        base_freq=4800.0,
        base_weight=0.2,
        ridge_freq=1200.0,
        ridge_weight=0.05,
        grid_freq=220.0,
        grid_weight=0.65,
        noise_weight=0.05,
        base_height=10.0,
        cmap="gray",
    ),
}

_PROFILE_ALIASES = {
    "desert_sand": "desert",
    "urban_asphalt": "urban",
    "mountain_rock": "mountain",
    "forest_loam": "forest",
    "default": "rolling",
}


def _resolve_profile(
    profile: TerrainProfile | str | None,
    seed: int | None,
) -> TerrainProfile:
    if isinstance(profile, TerrainProfile):
        return profile
    key = "rolling"
    if profile is not None:
        key = str(profile).strip().lower()
    key = _PROFILE_ALIASES.get(key, key)
    if key in {"auto", "random"}:
        names = [name for name in TERRAIN_PROFILES if name != "rolling"]
        if not names:
            return TERRAIN_PROFILES["rolling"]
        rng = random.Random(int(seed)) if seed is not None else random.Random()
        key = rng.choice(names)
    return TERRAIN_PROFILES.get(key, TERRAIN_PROFILES["rolling"])


def _resolve_color_range(
    profile: TerrainProfile,
    seed: int | None,
    z_grid: _F64Arr,
) -> tuple[float, float]:
    global _last_color_key, _last_color_range
    key = (profile.name, int(seed) if seed is not None else -1)
    if _last_color_key == key and _last_color_range is not None:
        return _last_color_range
    if z_grid.size:
        z_min = float(np.nanmin(z_grid))
        z_max = float(np.nanmax(z_grid))
    else:
        z_min = float(_cfg.TERRAIN_ZMIN)
        z_max = float(_cfg.TERRAIN_ZMAX)
    if not np.isfinite(z_min) or not np.isfinite(z_max) or z_min == z_max:
        z_min = float(_cfg.TERRAIN_ZMIN)
        z_max = float(_cfg.TERRAIN_ZMAX)
    _last_color_key = key
    _last_color_range = (z_min, z_max)
    return z_min, z_max

# ─────────────────────────────────────────────────────────────────────────────
# 1. Height-field generator
# ─────────────────────────────────────────────────────────────────────────────
def generate_terrain(
    xmin: float = _cfg.TERRAIN_XMIN,
    xmax: float = _cfg.TERRAIN_XMAX,
    ymin: float = _cfg.TERRAIN_YMIN,
    ymax: float = _cfg.TERRAIN_YMAX,
    step: int = _cfg.TERRAIN_STEP,
    amplitude: float | None = None,
    *,
    profile: TerrainProfile | str | None = None,
    seed: int | None = None,
) -> tuple[_F64Arr, _F64Arr, _F64Arr]:
    """
    Return (x_grid, y_grid, z_grid) arrays describing a rolling height-field.
    """
    try:
        profile_obj = _resolve_profile(profile, seed)
        if amplitude is None:
            amplitude = profile_obj.amplitude
        amplitude = float(amplitude)
        if step < 2 or amplitude < 0 or xmin >= xmax or ymin >= ymax:
            raise ValueError("invalid terrain parameters")

        grid = np.meshgrid(
            np.linspace(xmin, xmax, step),
            np.linspace(ymin, ymax, step),
        )
        gx, gy = grid[0], grid[1]
        base_freq = max(1.0, profile_obj.base_freq)
        ridge_freq = max(1.0, profile_obj.ridge_freq)
        grid_freq = max(1.0, profile_obj.grid_freq)

        base = np.sin(gx / base_freq) * np.cos(gy / base_freq)
        ridge = np.abs(np.sin(gx / ridge_freq) * np.cos(gy / ridge_freq))
        grid_pat = np.sin(gx / grid_freq) * np.sin(gy / grid_freq)

        rng = np.random.default_rng(seed if seed is not None else 42)
        noise = rng.standard_normal((step, step))

        height = profile_obj.base_height + amplitude * (
            profile_obj.base_weight * base
            + profile_obj.ridge_weight * ridge
            + profile_obj.grid_weight * grid_pat
            + profile_obj.noise_weight * noise
        )
        height = np.clip(height, _cfg.TERRAIN_ZMIN, _cfg.TERRAIN_ZMAX)
        return grid[0], grid[1], height

    except Exception:                                 # pragma: no cover
        empty = np.empty((0, 0), dtype=np.float64)
        return empty, empty, empty


def _effective_grid(step: int, rcount: int, ccount: int) -> tuple[int, int, int]:
    step = max(2, int(step))
    rcount = max(2, int(rcount))
    ccount = max(2, int(ccount))
    rcount = min(rcount, step)
    ccount = min(ccount, step)
    render_step = max(rcount, ccount)
    if step > render_step:
        step = render_step
    return step, rcount, ccount


# ─────────────────────────────────────────────────────────────────────────────
# 2. Convenience helper – draw straight onto an Axes3D
# ─────────────────────────────────────────────────────────────────────────────
@overload
def draw_terrain(
    ax: Axes3D,
    *,
    xmin: float = ...,
    xmax: float = ...,
    ymin: float = ...,
    ymax: float = ...,
    step: int = ...,
    amplitude: float | None = ...,
    cmap: str | None = ...,
    alpha: float | None = ...,
    edgecolor: str | None = ...,
    rcount: int = ...,
    ccount: int = ...,
    plot_kw: _PlotKw | None = ...,
    profile: TerrainProfile | str | None = ...,
    seed: int | None = ...,
    return_surface: Literal[False] = ...,
) -> tuple[_F64Arr, _F64Arr, _F64Arr]: ...

@overload
def draw_terrain(
    ax: Axes3D,
    *,
    xmin: float = ...,
    xmax: float = ...,
    ymin: float = ...,
    ymax: float = ...,
    step: int = ...,
    amplitude: float | None = ...,
    cmap: str | None = ...,
    alpha: float | None = ...,
    edgecolor: str | None = ...,
    rcount: int = ...,
    ccount: int = ...,
    plot_kw: _PlotKw | None = ...,
    profile: TerrainProfile | str | None = ...,
    seed: int | None = ...,
    return_surface: Literal[True],
) -> tuple[_F64Arr, _F64Arr, _F64Arr, Any]: ...

def draw_terrain(
    ax: Axes3D,
    *,
    xmin: float = _cfg.TERRAIN_XMIN,
    xmax: float = _cfg.TERRAIN_XMAX,
    ymin: float = _cfg.TERRAIN_YMIN,
    ymax: float = _cfg.TERRAIN_YMAX,
    step: int = _cfg.TERRAIN_STEP,
    amplitude: float | None = None,
    cmap: str | None = None,
    alpha: float | None = None,
    edgecolor: str | None = None,
    rcount: int = _cfg.TERRAIN_RCOUNT,
    ccount: int = _cfg.TERRAIN_CCOUNT,
    plot_kw: _PlotKw | None = None,
    profile: TerrainProfile | str | None = None,
    seed: int | None = None,
    return_surface: bool = False,
) -> tuple[_F64Arr, _F64Arr, _F64Arr] | tuple[_F64Arr, _F64Arr, _F64Arr, Any]:
    """
    Generate terrain and immediately add it to *ax* via ``plot_surface``.
    Returns the (x, y, z) arrays in case the caller needs them.
    """
    step, rcount, ccount = _effective_grid(step, rcount, ccount)

    profile_obj = _resolve_profile(profile, seed)
    if cmap is None:
        cmap = profile_obj.cmap
    if alpha is None:
        alpha = _cfg.TERRAIN_ALPHA if profile_obj.alpha is None else profile_obj.alpha
    if edgecolor is None:
        edgecolor = "none" if profile_obj.edgecolor is None else profile_obj.edgecolor

    terrain = generate_terrain(
        xmin=xmin, xmax=xmax, ymin=ymin, ymax=ymax,
        step=step, amplitude=amplitude,
        profile=profile_obj,
        seed=seed,
    )
    set_active_terrain(terrain[0], terrain[1], terrain[2])
    z_min, z_max = _resolve_color_range(profile_obj, seed, terrain[2])

    ax_any = cast(Any, ax)
    surface = ax_any.plot_surface(
        *terrain,
        cmap=cmap,
        vmin=z_min,
        vmax=z_max,
        alpha=alpha,
        edgecolor=edgecolor,
        rcount=rcount,
        ccount=ccount,
        shade=_cfg.TERRAIN_SHADE,
        antialiased=_cfg.TERRAIN_ANTIALIASED,
        **(plot_kw or {}),
    )
    if return_surface:
        return terrain[0], terrain[1], terrain[2], surface
    return terrain
