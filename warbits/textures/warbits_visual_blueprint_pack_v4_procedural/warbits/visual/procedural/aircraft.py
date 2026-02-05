from __future__ import annotations

from dataclasses import dataclass
from typing import Any, List, Mapping, Optional, Sequence

import math
import numpy as np
from numpy.typing import NDArray

from warbits.visual.blueprint_schema import Blueprint
from .dimensions import Dimensions, dims_from_mapping
from .primitives import Edge, cone, cylinder, merge

NDArrayFloat = NDArray[np.float64]


@dataclass(frozen=True)
class JetParams:
    """High-level parameters for a stylized jet wireframe.

    Coordinate system for output:
      - +x = forward
      - +y = left
      - +z = up
    """
    length_m: float = 15.0
    wingspan_m: float = 10.0
    height_m: float = 4.0

    fuselage_radius_m: Optional[float] = None  # if None, derived

    # Wing shape: these are fractions of length/span to keep everything stable.
    wing_x_center_frac: float = 0.05   # where wings attach relative to center (0 = mid)
    wing_root_chord_frac: float = 0.28 # chord length relative to overall length
    wing_tip_chord_frac: float = 0.16
    wing_sweep_deg: float = 26.0

    # Tail
    twin_tail: bool = True
    tail_cant_deg: float = 25.0
    tail_height_frac: float = 0.35
    hstab_span_frac: float = 0.32

    # Detail knobs
    canopy: bool = True
    ribs: int = 2  # how many fuselage/wing ribs
    segment_quality: int = 10  # circle segments for cylindrical pieces


def _safe(v: float, lo: float, hi: float) -> float:
    return float(min(max(v, lo), hi))


def jet_params_from_spec(spec: Mapping[str, Any], *, defaults: JetParams = JetParams()) -> JetParams:
    """Derive JetParams from a DataStore-ish vehicle spec.

    This is deliberately tolerant:
    - if wingspan is missing, we will infer from width/length.
    - if fuselage radius is missing, infer from width/height.

    Expected keys (any subset):
    - length_m, wingspan_m, height_m, width_m
    - plus optional shape flags like twin_tail.

    Returns:
        JetParams usable for procedural blueprint generation.
    """
    dims = dims_from_mapping(spec, defaults=Dimensions(
        length_m=defaults.length_m,
        width_m=max(1.5, defaults.wingspan_m),   # for aircraft, width is ambiguous; keep sane
        height_m=defaults.height_m,
        wingspan_m=defaults.wingspan_m,
    ))

    length = dims.length_m
    wingspan = dims.wingspan_m
    height = dims.height_m

    # Heuristic: if a "wingspan" isn't present, treat width as span if it's large.
    if wingspan is None:
        if dims.width_m >= 4.0:
            wingspan = dims.width_m
        else:
            wingspan = max(0.65 * length, 8.0)

    # Fuselage radius estimate: prefer a small fraction of wingspan, clamp to sane values.
    fuse_r = 0.09 * float(wingspan)
    fuse_r = _safe(fuse_r, 0.35, 1.6)

    # Twin tail guess: if spec includes any explicit tag
    twin = defaults.twin_tail
    for k in ("twin_tail", "twinVerticalTail", "twin_vertical_tail"):
        if k in spec and spec[k] is not None:
            try:
                twin = bool(spec[k])
            except Exception:
                pass

    # Sweep guess: some datasets include this; otherwise keep default.
    sweep = defaults.wing_sweep_deg
    for k in ("wing_sweep_deg", "sweep_deg", "Wing Sweep"):
        if k in spec and spec[k] is not None:
            try:
                sweep = float(spec[k])
            except Exception:
                continue
            if math.isfinite(sweep):
                sweep = _safe(sweep, 10.0, 60.0)
                break

    # Clamp core dims
    length = _safe(length, 5.0, 50.0)
    wingspan = _safe(float(wingspan), 4.0, 45.0)
    height = _safe(height, 1.0, 15.0)

    return JetParams(
        length_m=length,
        wingspan_m=wingspan,
        height_m=height,
        fuselage_radius_m=fuse_r,
        wing_sweep_deg=sweep,
        twin_tail=twin,
    )


def build_jet_blueprint(
    blueprint_id: str,
    params: JetParams,
    *,
    tags: Optional[Sequence[str]] = None,
) -> Blueprint:
    """Build a readable jet-like wireframe blueprint.

    This is *not* trying to exactly replicate a specific aircraft model; it's a
    stylized tactical wireframe with dimension-respecting proportions.

    Output:
    - high detail edges (edges)
    - lod_edges["silhouette"]: minimal outline
    - lod_edges["low"]: a mid-tier of structure
    """
    L = float(params.length_m)
    S = float(params.wingspan_m)
    H = float(params.height_m)
    r = float(params.fuselage_radius_m or (0.09 * S))

    segq = int(max(6, params.segment_quality))

    # Model anchored around origin; nose is +x.
    # Fuselage: center at x=0, length L*0.9 (nose cone handles remainder).
    fuse_len = 0.90 * L
    nose_len = 0.10 * L
    fuse_center = (0.0, 0.0, 0.35 * r)

    parts: List[tuple[NDArrayFloat, List[Edge]]] = []
    V_fuse, E_fuse = cylinder(fuse_center, radius=r, length=fuse_len, axis="x", segments=segq, caps=True)
    # Nose base at +fuse_len/2; cone points forward.
    nose_base = (0.5 * fuse_len, 0.0, 0.35 * r)
    V_nose, E_nose = cone(nose_base, radius=0.85 * r, length=nose_len, axis="x", segments=segq)
    parts.append((V_fuse, E_fuse))
    parts.append((V_nose, E_nose))

    # Wings (simple trapezoid each side)
    wing_x = params.wing_x_center_frac * L
    sweep = math.radians(float(params.wing_sweep_deg))
    root_chord = params.wing_root_chord_frac * L
    tip_chord = params.wing_tip_chord_frac * L
    half_span = 0.5 * S

    # Wing y positions: slightly below canopy for a slick look
    wing_z = 0.15 * r

    # Compute leading edge offset due to sweep: tip LE back by tan(sweep) * half_span
    le_back = math.tan(sweep) * half_span

    # Left wing points (y positive)
    # Define root LE at (wing_x + root_chord/2, 0, wing_z)
    # ... But we want wing_x to be about mid-chord. We'll place LE and TE around it.
    x_root_le = wing_x + 0.50 * root_chord
    x_root_te = wing_x - 0.50 * root_chord
    x_tip_le = x_root_le - le_back
    x_tip_te = x_tip_le - tip_chord

    # Create vertices (root LE/TE, tip LE/TE)
    V_wl = np.array([
        [x_root_le,  0.18 * r, wing_z],
        [x_root_te,  0.18 * r, wing_z],
        [x_tip_te,   half_span, wing_z],
        [x_tip_le,   half_span, wing_z],
    ], dtype=float)
    # Mirror to right wing
    V_wr = V_wl.copy()
    V_wr[:, 1] *= -1.0

    # Wing edges: outline
    E_wing = [(0, 3), (3, 2), (2, 1), (1, 0)]  # loop

    # Add ribs as sparse internal structure
    E_wing_detail: List[Edge] = []
    # Rib lines from root to tip across chord
    for t in np.linspace(0.25, 0.75, int(max(0, params.ribs))):
        # interpolate between leading and trailing edges
        # at root and tip
        root = (1.0 - t) * V_wl[0] + t * V_wl[1]
        tip = (1.0 - t) * V_wl[3] + t * V_wl[2]
        # add as new vertices
        idx0 = len(V_wl)
        V_wl = np.vstack([V_wl, root, tip])
        E_wing_detail.append((idx0, idx0 + 1))

    V_wl, E_wl = V_wl, (E_wing + E_wing_detail)
    V_wr, E_wr = V_wr, (E_wing + [(a, b) for a, b in E_wing_detail])  # indices will shift after merge anyway

    parts.append((V_wl, E_wl))
    parts.append((V_wr, E_wr))

    # Horizontal stabilizers (simple triangle-ish)
    hspan = params.hstab_span_frac * S * 0.5
    hchord = 0.18 * L
    tail_x = -0.45 * fuse_len
    h_z = 0.40 * r
    V_hl = np.array([
        [tail_x + 0.45 * hchord,  0.15 * r, h_z],
        [tail_x - 0.55 * hchord,  0.15 * r, h_z],
        [tail_x - 0.15 * hchord,  hspan,    h_z],
    ], dtype=float)
    V_hr = V_hl.copy()
    V_hr[:, 1] *= -1.0
    E_h = [(0, 2), (2, 1), (1, 0)]
    parts.append((V_hl, E_h))
    parts.append((V_hr, E_h))

    # Vertical tail(s)
    tail_height = params.tail_height_frac * H
    vt_base_x = -0.48 * fuse_len
    vt_base_z = 0.65 * r
    cant = math.radians(float(params.tail_cant_deg))
    # base y offset for twin tail
    vt_y_off = 0.45 * r if params.twin_tail else 0.0

    def _vtail(y_sign: float) -> tuple[NDArrayFloat, List[Edge]]:
        base = np.array([vt_base_x, y_sign * vt_y_off, vt_base_z], dtype=float)
        tip = base + np.array([-0.12 * L, y_sign * math.sin(cant) * 0.65 * r, tail_height], dtype=float)
        # small trailing edge point
        back = base + np.array([-0.05 * L, y_sign * 0.10 * r, 0.25 * tail_height], dtype=float)
        V = np.vstack([base, tip, back])
        E = [(0, 1), (1, 2), (2, 0)]
        return np.asarray(V, dtype=float), E

    if params.twin_tail:
        parts.append(_vtail(+1.0))
        parts.append(_vtail(-1.0))
    else:
        # single tail centered
        parts.append(_vtail(0.0))

    # Canopy loop (small, readable)
    if params.canopy:
        cx = 0.18 * L
        cz = vt_base_z + 0.75 * r
        cy = 0.0
        canopy = np.array([
            [cx + 0.06 * L, cy,           cz + 0.06 * r],
            [cx + 0.02 * L, cy + 0.8 * r, cz + 0.02 * r],
            [cx - 0.08 * L, cy + 0.75 * r, cz - 0.02 * r],
            [cx - 0.12 * L, cy,           cz + 0.00 * r],
            [cx - 0.08 * L, cy - 0.75 * r, cz - 0.02 * r],
            [cx + 0.02 * L, cy - 0.8 * r, cz + 0.02 * r],
        ], dtype=float)
        E_can = [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 0)]
        parts.append((canopy, E_can))

    V, E = merge(parts)

    # Compute LOD edges. We want "silhouette" to be mostly the major outlines.
    # We'll include: fuselage centerline, wing outlines, tail outlines.
    # The easiest stable approximation is: choose the longest edges.
    lengths: List[tuple[int, float]] = []
    for i, (a, b) in enumerate(E):
        pa = V[a]
        pb = V[b]
        lengths.append((i, float(np.linalg.norm(pb - pa))))
    lengths.sort(key=lambda t: t[1], reverse=True)
    # silhouette: top N edges
    sil_n = min(120, max(40, int(0.35 * len(E))))
    low_n = min(220, max(80, int(0.60 * len(E))))
    E_sil = [E[i] for i, _ in lengths[:sil_n]]
    E_low = [E[i] for i, _ in lengths[:low_n]]

    # Tags
    t = set(tags or [])
    t.update(["aircraft", "jet", "wireframe"])
    if params.twin_tail:
        t.add("twin_tail")
    else:
        t.add("single_tail")

    return Blueprint(
        blueprint_id=blueprint_id,
        kind="aircraft",
        tags=sorted(t),
        vertices_m=[(float(x), float(y), float(z)) for x, y, z in V],
        edges=[(int(a), int(b)) for a, b in E],
        lod_edges={
            "low": tuple((int(a), int(b)) for a, b in E_low),
            "silhouette": tuple((int(a), int(b)) for a, b in E_sil),
        },
        meta={
            "source": "procedural",
            "generator": "build_jet_blueprint",
            "params": {
                "length_m": L,
                "wingspan_m": S,
                "height_m": H,
                "fuselage_radius_m": r,
            },
        },
    )
