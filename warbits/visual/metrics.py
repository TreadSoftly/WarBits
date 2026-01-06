"""warbits.visual.metrics

Compute structural metrics for Blueprint objects.

Used for:
- performance budgeting (edge/vertex counts)
- build QA (bounds sanity)
- atlas labeling
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Sequence, Tuple

import math

from .blueprint_schema import Blueprint, Vec3
from .budgets import normalize_lod_name, select_edges_for_lod


@dataclass(frozen=True)
class BlueprintMetrics:
    blueprint_id: str
    kind: str
    tags: Tuple[str, ...]
    vertices: int
    edges: int
    bbox_min: Tuple[float, float, float]
    bbox_max: Tuple[float, float, float]
    span: Tuple[float, float, float]  # dx, dy, dz
    approx_radius_m: float  # for LOD distance heuristics

    def to_dict(self) -> Dict[str, object]:
        return {
            "blueprint_id": self.blueprint_id,
            "kind": self.kind,
            "tags": list(self.tags),
            "vertices": self.vertices,
            "edges": self.edges,
            "bbox_min": list(self.bbox_min),
            "bbox_max": list(self.bbox_max),
            "span": list(self.span),
            "approx_radius_m": float(self.approx_radius_m),
        }


def compute_bbox(vertices: Sequence[Vec3]) -> Tuple[Tuple[float, float, float], Tuple[float, float, float]]:
    xs = [v[0] for v in vertices]
    ys = [v[1] for v in vertices]
    zs = [v[2] for v in vertices]
    return (min(xs), min(ys), min(zs)), (max(xs), max(ys), max(zs))


def compute_radius(span: Tuple[float, float, float]) -> float:
    dx, dy, dz = span
    # Half diagonal of AABB
    return 0.5 * math.sqrt(dx * dx + dy * dy + dz * dz)


def compute_metrics(bp: Blueprint, lod: str = "lod0") -> BlueprintMetrics:
    lod = normalize_lod_name(lod)
    edges = select_edges_for_lod(bp, lod)
    bmin, bmax = compute_bbox(bp.vertices_m)
    span = (bmax[0] - bmin[0], bmax[1] - bmin[1], bmax[2] - bmin[2])
    radius = compute_radius(span)

    return BlueprintMetrics(
        blueprint_id=bp.blueprint_id,
        kind=bp.kind,
        tags=tuple(bp.tags or ()),
        vertices=len(bp.vertices_m),
        edges=len(edges),
        bbox_min=bmin,
        bbox_max=bmax,
        span=span,
        approx_radius_m=radius,
    )
