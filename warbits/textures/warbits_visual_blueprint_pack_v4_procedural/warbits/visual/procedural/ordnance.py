from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Sequence

import numpy as np
from numpy.typing import NDArray

from warbits.visual.blueprint_schema import Blueprint

from .primitives import cone, cylinder, merge

NDArrayFloat = NDArray[np.float64]


@dataclass(frozen=True)
class MissileParams:
    length_m: float = 3.0
    diameter_m: float = 0.22
    fin_span_m: float = 0.55
    segments: int = 10


@dataclass(frozen=True)
class RocketParams:
    length_m: float = 2.0
    diameter_m: float = 0.14
    fin_span_m: float = 0.35
    segments: int = 9


@dataclass(frozen=True)
class BombParams:
    length_m: float = 2.6
    diameter_m: float = 0.35
    tail_span_m: float = 0.55
    segments: int = 10


def build_missile_blueprint(
    blueprint_id: str,
    params: MissileParams,
    *,
    tags: Optional[Sequence[str]] = None,
) -> Blueprint:
    L = float(params.length_m)
    d = float(params.diameter_m)
    r = 0.5 * d
    seg = int(max(6, params.segments))

    body_len = 0.88 * L
    nose_len = 0.12 * L
    body_center = (0.0, 0.0, 0.0)

    V_body, E_body = cylinder(body_center, radius=r, length=body_len, axis="x", segments=seg, caps=True)
    nose_base = (0.5 * body_len, 0.0, 0.0)
    V_nose, E_nose = cone(nose_base, radius=0.85 * r, length=nose_len, axis="x", segments=seg)

    # Simple fins at the rear
    fin_span = float(params.fin_span_m)
    fin_x = -0.5 * body_len + 0.10 * L
    fin = np.array(
        [
            [fin_x, 0.0, 0.0],
            [fin_x - 0.12 * L, 0.5 * fin_span, 0.0],
            [fin_x - 0.08 * L, 0.0, 0.5 * fin_span],
            [fin_x - 0.12 * L, -0.5 * fin_span, 0.0],
            [fin_x - 0.08 * L, 0.0, -0.5 * fin_span],
        ],
        dtype=float,
    )
    E_fin = [(0, 1), (0, 2), (0, 3), (0, 4), (1, 2), (2, 3), (3, 4), (4, 1)]

    V, E = merge([(V_body, E_body), (V_nose, E_nose), (fin, E_fin)])

    # LOD edges: keep body + nose outlines only
    # Choose by length: works well for ordnance.
    lengths: list[tuple[int, float]] = []
    for i, (a, b) in enumerate(E):
        lengths.append((i, float(np.linalg.norm(V[b] - V[a]))))
    lengths.sort(key=lambda t: t[1], reverse=True)
    sil_n = min(70, max(18, int(0.45 * len(E))))
    low_n = min(110, max(28, int(0.70 * len(E))))
    E_sil = [E[i] for i, _ in lengths[:sil_n]]
    E_low = [E[i] for i, _ in lengths[:low_n]]

    t = set(tags or [])
    t.update(["ordnance", "missile", "wireframe"])

    return Blueprint(
        blueprint_id=blueprint_id,
        kind="ordnance",
        tags=sorted(t),
        vertices_m=[(float(x), float(y), float(z)) for x, y, z in V],
        edges=[(int(a), int(b)) for a, b in E],
        lod_edges={
            "low": tuple((int(a), int(b)) for a, b in E_low),
            "silhouette": tuple((int(a), int(b)) for a, b in E_sil),
        },
        meta={
            "source": "procedural",
            "generator": "build_missile_blueprint",
            "params": {"length_m": L, "diameter_m": d},
        },
    )


def build_rocket_blueprint(
    blueprint_id: str,
    params: RocketParams,
    *,
    tags: Optional[Sequence[str]] = None,
) -> Blueprint:
    # Rockets are basically stubby missiles with smaller fins.
    mp = MissileParams(
        length_m=params.length_m,
        diameter_m=params.diameter_m,
        fin_span_m=params.fin_span_m,
        segments=params.segments,
    )
    bp = build_missile_blueprint(blueprint_id, mp, tags=tags)
    # Replace tags for clarity
    t = set(bp.tags)
    t.discard("missile")
    t.add("rocket")
    return Blueprint(
        blueprint_id=bp.blueprint_id,
        kind=bp.kind,
        tags=sorted(t),
        vertices_m=bp.vertices_m,
        edges=bp.edges,
        lod_edges=bp.lod_edges,
        meta={**bp.meta, "generator": "build_rocket_blueprint"},
    )


def build_bomb_blueprint(
    blueprint_id: str,
    params: BombParams,
    *,
    tags: Optional[Sequence[str]] = None,
) -> Blueprint:
    L = float(params.length_m)
    d = float(params.diameter_m)
    r = 0.5 * d
    seg = int(max(6, params.segments))

    # Body: slightly longer cylinder
    body_len = 0.82 * L
    nose_len = 0.10 * L
    tail_len = 0.08 * L
    body_center = (0.0, 0.0, 0.0)

    V_body, E_body = cylinder(body_center, radius=r, length=body_len, axis="x", segments=seg, caps=True)
    nose_base = (0.5 * body_len, 0.0, 0.0)
    V_nose, E_nose = cone(nose_base, radius=0.92 * r, length=nose_len, axis="x", segments=seg)

    # Tail: simple fin cross
    tail_span = float(params.tail_span_m)
    tx = -0.5 * body_len - 0.02 * L
    tail = np.array(
        [
            [tx, 0.0, 0.0],
            [tx - tail_len, 0.5 * tail_span, 0.0],
            [tx - tail_len, -0.5 * tail_span, 0.0],
            [tx - tail_len, 0.0, 0.5 * tail_span],
            [tx - tail_len, 0.0, -0.5 * tail_span],
        ],
        dtype=float,
    )
    E_tail = [(0, 1), (0, 2), (0, 3), (0, 4), (1, 3), (3, 2), (2, 4), (4, 1)]

    V, E = merge([(V_body, E_body), (V_nose, E_nose), (tail, E_tail)])

    # LOD: prefer outlines
    lengths: list[tuple[int, float]] = []
    for i, (a, b) in enumerate(E):
        lengths.append((i, float(np.linalg.norm(V[b] - V[a]))))
    lengths.sort(key=lambda t: t[1], reverse=True)
    sil_n = min(70, max(18, int(0.45 * len(E))))
    low_n = min(110, max(28, int(0.70 * len(E))))
    E_sil = [E[i] for i, _ in lengths[:sil_n]]
    E_low = [E[i] for i, _ in lengths[:low_n]]

    t = set(tags or [])
    t.update(["ordnance", "bomb", "wireframe"])

    return Blueprint(
        blueprint_id=blueprint_id,
        kind="ordnance",
        tags=sorted(t),
        vertices_m=[(float(x), float(y), float(z)) for x, y, z in V],
        edges=[(int(a), int(b)) for a, b in E],
        lod_edges={
            "low": tuple((int(a), int(b)) for a, b in E_low),
            "silhouette": tuple((int(a), int(b)) for a, b in E_sil),
        },
        meta={"source": "procedural", "generator": "build_bomb_blueprint", "params": {"length_m": L, "diameter_m": d}},
    )
