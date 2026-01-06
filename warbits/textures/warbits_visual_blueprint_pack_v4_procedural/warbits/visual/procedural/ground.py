from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Optional, Sequence, Tuple, List

import numpy as np

from ..blueprint_schema import Blueprint
from .dimensions import Dimensions, dims_from_mapping
from .primitives import Edge, box, cylinder, merge


@dataclass(frozen=True)
class TankParams:
    """High-level parameters for a tank/APC-ish ground unit."""
    length_m: float = 7.5
    width_m: float = 3.5
    height_m: float = 2.6

    turret_radius_m: Optional[float] = None
    turret_height_frac: float = 0.35
    turret_x_frac: float = 0.10

    barrel_length_frac: float = 0.55
    barrel_radius_frac: float = 0.06

    # Detail knobs
    rib_count: int = 2
    cylinder_segments: int = 10


def tank_params_from_spec(spec: Mapping[str, Any], *, defaults: TankParams = TankParams()) -> TankParams:
    dims = dims_from_mapping(spec, defaults=Dimensions(
        length_m=defaults.length_m,
        width_m=defaults.width_m,
        height_m=defaults.height_m,
    ))
    L = float(min(max(dims.length_m, 2.5), 20.0))
    W = float(min(max(dims.width_m, 1.2), 8.0))
    H = float(min(max(dims.height_m, 1.0), 5.0))
    turret_r = 0.33 * W if defaults.turret_radius_m is None else float(defaults.turret_radius_m)
    turret_r = float(min(max(turret_r, 0.35), 2.5))
    return TankParams(length_m=L, width_m=W, height_m=H, turret_radius_m=turret_r)


def build_tank_blueprint(
    blueprint_id: str,
    params: TankParams,
    *,
    tags: Optional[Sequence[str]] = None,
) -> Blueprint:
    """Build a stylized tank wireframe blueprint."""
    L, W, H = float(params.length_m), float(params.width_m), float(params.height_m)
    seg = int(max(6, params.cylinder_segments))

    # Hull box
    hull_center = (0.0, 0.0, 0.5 * H)
    V_hull, E_hull = box(hull_center, (L, W, H))

    # Turret: short cylinder
    tr = float(params.turret_radius_m or (0.33 * W))
    th = params.turret_height_frac * H
    tx = params.turret_x_frac * L
    V_tur, E_tur = cylinder((tx, 0.0, H + 0.5 * th), radius=tr, length=th, axis="z", segments=seg, caps=True)

    # Barrel: thin cylinder along +x from turret center
    bl = params.barrel_length_frac * L
    br = params.barrel_radius_frac * tr
    barrel_center = (tx + 0.5 * bl + tr * 0.4, 0.0, H + 0.5 * th)
    V_bar, E_bar = cylinder(barrel_center, radius=br, length=bl, axis="x", segments=max(6, seg // 2), caps=False)

    # Tracks hints: lines along sides near ground
    z_track = 0.15 * H
    y_track = 0.5 * W * 0.92
    track = np.array([
        [ 0.48 * L,  y_track, z_track],
        [-0.48 * L,  y_track, z_track],
        [-0.48 * L,  y_track, z_track + 0.15 * H],
        [ 0.48 * L,  y_track, z_track + 0.15 * H],
    ], dtype=float)
    E_track = [(0, 1), (1, 2), (2, 3), (3, 0)]
    track_r = track.copy()
    track_r[:, 1] *= -1.0

    parts = [
        (V_hull, E_hull),
        (V_tur, E_tur),
        (V_bar, E_bar),
        (track, E_track),
        (track_r, E_track),
    ]
    V, E = merge(parts)

    # LOD edges by length
    lengths = []
    for i, (a, b) in enumerate(E):
        pa = V[a]; pb = V[b]
        lengths.append((i, float(np.linalg.norm(pb - pa))))
    lengths.sort(key=lambda t: t[1], reverse=True)
    sil_n = min(90, max(30, int(0.40 * len(E))))
    low_n = min(150, max(60, int(0.65 * len(E))))
    E_sil = [E[i] for i, _ in lengths[:sil_n]]
    E_low = [E[i] for i, _ in lengths[:low_n]]

    t = set(tags or [])
    t.update(["ground", "armored", "wireframe"])

    return Blueprint(
        blueprint_id=blueprint_id,
        kind="ground",
        tags=sorted(t),
        vertices_m=V,
        edges=E,
        lod_edges={"low": E_low, "silhouette": E_sil},
        meta={
            "source": "procedural",
            "generator": "build_tank_blueprint",
            "params": {"length_m": L, "width_m": W, "height_m": H},
        },
    )
