# ── warbits/logic/aircraft.py ───────────────────────────────────────────────

from __future__ import annotations

import math
from types import MethodType
from typing import Any, List, Tuple, cast

import numpy as np
from mpl_toolkits.mplot3d import Axes3D              # type: ignore
from mpl_toolkits.mplot3d.art3d import Poly3DCollection  # type: ignore
from numpy.typing import NDArray

from ..rendering.geometry import transform_faces as _transform_faces

__all__ = [
    # mesh factories
    "build_mesh_faces",
    "create_aircraft_model",
    "create_bogie_model",
    "update_mesh",
    # config
    "AIRCRAFT_SCALE",
    "BOGIE_SCALE",
    # runtime helpers
    "register_axes",
    "reset_aircraft",
    "step_aircraft",
]

AIRCRAFT_SCALE = 115.0
BOGIE_SCALE = AIRCRAFT_SCALE

_Faces = NDArray[np.float32] | List[List[Tuple[float, float, float]]]

# ───────────────────── helper – verts cache attachment ──────────────────────
def _attach_vert_cache(
    poly: Poly3DCollection,
    faces: _Faces,
) -> None:
    poly._warbits_faces = faces  # type: ignore[attr-defined]

    if not hasattr(poly, "get_verts"):
        poly.get_verts = MethodType(          # type: ignore[attr-defined]
            lambda self: self._warbits_faces, poly  # type: ignore[attr-defined]
        )

    _orig = poly.set_verts

    def _wrapped(  # type: ignore[override]
        self: Poly3DCollection,
        new_faces: _Faces,
        *args: Any,
        closed: bool = False,
        **kwargs: Any,
    ):
        self._warbits_faces = new_faces      # type: ignore[attr-defined]
        return _orig(cast(Any, new_faces), *args, closed=closed, **kwargs)

    poly.set_verts = MethodType(_wrapped, poly)      # type: ignore[attr-defined]

# ───────────────────────── base mesh generator ──────────────────────────────
def build_mesh_faces(
    position: Tuple[float, float, float],
    direction: Tuple[float, float, float],
    *,
    scale: float,
) -> List[List[Tuple[float, float, float]]]:
    px, py, pz = position
    dx, dy, dz = direction

    mag = math.sqrt(dx * dx + dy * dy + dz * dz)
    if mag < 1e-6:
        dx, dy, dz, mag = 1.0, 0.0, 0.0, 1.0
    dx, dy, dz = dx / mag, dy / mag, dz / mag

    sc = float(scale)
    nose   = ( 1.50 * sc,  0.0,  0.15 * sc)
    wing_l = ( 0.00 * sc, -0.8 * sc, 0.15 * sc)
    wing_r = ( 0.00 * sc,  0.8 * sc, 0.15 * sc)
    tail   = (-1.30 * sc,  0.0,  0.15 * sc)
    thick  = -0.15 * sc

    top: List[Tuple[float, float, float]] = [nose, wing_r, tail, wing_l]
    bot: List[Tuple[float, float, float]] = [(x, y, thick) for x, y, _ in top]
    faces: List[List[Tuple[float, float, float]]] = [top, bot]
    for i in range(4):
        j = (i + 1) % 4
        faces.append([top[i], top[j], bot[j], bot[i]])

    fwd  = np.array([dx, dy, dz])
    up_g = np.array([0.0, 0.0, 1.0])
    side = np.cross(fwd, up_g)
    if (side_mag := np.linalg.norm(side)) < 1e-6:
        side = np.cross(fwd, [1.0, 0.0, 0.0])
        side_mag = np.linalg.norm(side)
    side /= side_mag
    up = np.cross(side, fwd)
    R = np.vstack([fwd, side, up]).T

    def _xf(pt: Tuple[float, float, float]) -> NDArray[np.float64]:
        return np.array([px, py, pz]) + R.dot(np.array(pt))

    mesh = [[tuple(_xf(v)) for v in face] for face in faces]
    return mesh


def _build_base_faces(scale: float) -> NDArray[np.float32]:
    sc = float(scale)
    nose   = ( 1.50 * sc,  0.0,  0.15 * sc)
    wing_l = ( 0.00 * sc, -0.8 * sc, 0.15 * sc)
    wing_r = ( 0.00 * sc,  0.8 * sc, 0.15 * sc)
    tail   = (-1.30 * sc,  0.0,  0.15 * sc)
    thick  = -0.15 * sc

    top = np.array([nose, wing_r, tail, wing_l], dtype=np.float32)
    bot = top.copy()
    bot[:, 2] = thick
    faces = np.stack(
        [
            top,
            bot,
            np.array([top[0], top[1], bot[1], bot[0]], dtype=np.float32),
            np.array([top[1], top[2], bot[2], bot[1]], dtype=np.float32),
            np.array([top[2], top[3], bot[3], bot[2]], dtype=np.float32),
            np.array([top[3], top[0], bot[0], bot[3]], dtype=np.float32),
        ],
        axis=0,
    )
    return faces


def _generate_mesh(
    position: Tuple[float, float, float],
    direction: Tuple[float, float, float],
    *,
    scale: float,
    color: str,
) -> Poly3DCollection:
    base = _build_base_faces(scale)
    mesh = np.empty_like(base)
    _transform_faces(base, position, direction, mesh)

    poly = Poly3DCollection(mesh, facecolor=color, alpha=1.0)
    poly.set_edgecolor((0, 0, 0, 1))          # type: ignore[arg-type]
    _attach_vert_cache(poly, mesh)
    poly._warbits_base = base                # type: ignore[attr-defined]
    poly._warbits_work = mesh                # type: ignore[attr-defined]
    return poly

# public wrappers ------------------------------------------------------------
def create_aircraft_model(
    position: Tuple[float, float, float],
    direction: Tuple[float, float, float],
    *,
    scale: float = AIRCRAFT_SCALE,
    color: str = "#00ff00",
) -> Poly3DCollection:
    """Player aircraft - bright green, slightly larger."""
    poly = _generate_mesh(position, direction, scale=scale, color=color)
    poly_any = cast(Any, poly)
    poly_any.set_edgecolor("#eaff00")  # highlight edge for visibility
    poly_any.set_linewidth(1.2)
    return poly


def create_bogie_model(
    position: Tuple[float, float, float],
    direction: Tuple[float, float, float],
    *,
    scale: float = BOGIE_SCALE,
    color: str = "#ff2b2b",
) -> Poly3DCollection:
    """Enemy bogie - bright red for visibility."""
    poly = _generate_mesh(position, direction, scale=scale, color=color)
    poly_any = cast(Any, poly)
    poly_any.set_edgecolor("#fff2a8")
    poly_any.set_linewidth(1.0)
    return poly


def update_mesh(
    poly: Poly3DCollection,
    position: Tuple[float, float, float],
    direction: Tuple[float, float, float],
    *,
    scale: float,
) -> None:
    base = getattr(poly, "_warbits_base", None)
    work = getattr(poly, "_warbits_work", None)
    if not isinstance(base, np.ndarray) or not isinstance(work, np.ndarray):
        poly.set_verts(build_mesh_faces(position, direction, scale=scale))  # type: ignore[arg-type]
        return
    base_f = cast(NDArray[np.float32], base)
    work_f = cast(NDArray[np.float32], work)
    _transform_faces(base_f, position, direction, work_f)
    poly.set_verts(cast(Any, work_f))

# ────────── runtime helpers for the *player* aircraft only ───────────────────
_ax: Axes3D | None = None
_aircraft_poly: Poly3DCollection | None = None
_aircraft_glow: Any | None = None
_pulse_phase = 0.0
_PULSE_SPEED = 0.06
_GLOW_BASE_SIZE = 140.0
_GLOW_PULSE_EXTRA = 120.0


def _pulse_value(phase: float) -> float:
    return 0.5 * (1.0 + math.sin(phase))


def _sync_poly_colors(poly_any: Any) -> None:
    facecolors = getattr(poly_any, "_facecolors", None)
    edgecolors = getattr(poly_any, "_edgecolors", None)
    if facecolors is not None:
        if hasattr(poly_any, "_facecolors3d"):
            poly_any._facecolors3d = facecolors
        if hasattr(poly_any, "_facecolor3d"):
            poly_any._facecolor3d = facecolors
        if hasattr(poly_any, "_facecolors2d"):
            poly_any._facecolors2d = facecolors
    if edgecolors is not None:
        if hasattr(poly_any, "_edgecolors3d"):
            poly_any._edgecolors3d = edgecolors
        if hasattr(poly_any, "_edgecolor3d"):
            poly_any._edgecolor3d = edgecolors
        if hasattr(poly_any, "_edgecolors2d"):
            poly_any._edgecolors2d = edgecolors


def _apply_pulse(poly: Poly3DCollection, t: float) -> tuple[float, float, float, float]:
    pulse = 0.12 + (0.28 * t)
    edge_pulse = min(1.0, pulse + 0.25)
    glow_pulse = min(1.0, pulse + 0.45)
    face = (pulse, 1.0, pulse, 1.0)
    edge = (edge_pulse, 1.0, edge_pulse, 1.0)
    glow = (glow_pulse, 1.0, glow_pulse, 1.0)
    count = 1
    base = getattr(poly, "_warbits_base", None)
    if isinstance(base, np.ndarray) and base.ndim >= 1:
        count = int(base.shape[0])
    else:
        try:
            count = len(poly.get_verts())  # type: ignore[arg-type]
        except Exception:
            count = 1
    if count < 1:
        count = 1
    facecolors = [face] * count
    edgecolors = [edge] * count
    poly_any = cast(Any, poly)
    poly_any.set_facecolor(facecolors)
    poly_any.set_edgecolor(edgecolors)
    poly_any.set_linewidth(1.2 + (1.6 * t))
    _sync_poly_colors(poly_any)
    return glow

def register_axes(ax: Axes3D) -> None:
    """Scene must call this once after creating its `Axes3D`."""
    global _ax
    _ax = ax


def reset_aircraft() -> None:
    """Hide/remove mesh - called on animation loop restart."""
    global _aircraft_poly, _aircraft_glow
    if _aircraft_poly is not None:
        try:
            _aircraft_poly.remove()
        except Exception:
            pass
    _aircraft_poly = None
    if _aircraft_glow is not None:
        try:
            _aircraft_glow.remove()
        except Exception:
            pass
    _aircraft_glow = None


def step_aircraft(
    position: Tuple[float, float, float],
    velocity : Tuple[float, float, float],
) -> None:
    """Create or update the (friendly) aircraft each frame."""
    global _aircraft_poly, _aircraft_glow, _pulse_phase
    if _ax is None:
        return

    if _aircraft_poly is None:
        _aircraft_poly = create_aircraft_model(position, velocity)
        _ax.add_collection3d(_aircraft_poly)       # type: ignore[arg-type]
    else:
        update_mesh(_aircraft_poly, position, velocity, scale=AIRCRAFT_SCALE)
    _pulse_phase = (_pulse_phase + _PULSE_SPEED) % (2.0 * math.pi)
    t = _pulse_value(_pulse_phase)
    color = _apply_pulse(_aircraft_poly, t)
    ax_any = cast(Any, _ax)
    if _aircraft_glow is None:
        _aircraft_glow = ax_any.scatter(
            [position[0]],
            [position[1]],
            [position[2]],
            s=[float(_GLOW_BASE_SIZE)],
            c=[color],
            alpha=0.95,
            depthshade=False,
        )
    else:
        try:
            _aircraft_glow._offsets3d = ([position[0]], [position[1]], [position[2]])
        except Exception:
            pass
        size = _GLOW_BASE_SIZE + (_GLOW_PULSE_EXTRA * t)
        try:
            _aircraft_glow.set_sizes([size])
        except Exception:
            pass
        try:
            _aircraft_glow.set_facecolor([color])
            _aircraft_glow.set_edgecolor([color])
        except Exception:
            pass
