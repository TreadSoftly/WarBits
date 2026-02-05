from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Tuple

import numpy as np
from numpy.typing import NDArray

try:
    import trimesh  # type: ignore[import-not-found]
except Exception:  # pragma: no cover
    trimesh = None  # type: ignore

NDArrayInt = NDArray[np.int32]


def require_trimesh() -> Any:
    if trimesh is None:
        raise ImportError("trimesh is required for visual blueprint ingestion. " "Install with: pip install trimesh")
    return trimesh


@dataclass(frozen=True)
class LODSpec:
    name: str
    feature_angle_deg: float
    max_edges: int
    sample_rate: float = 1.0
    include_boundary: bool = True
    include_ribs: bool = False
    ribs_slices: int = 0


def extract_wireframe_edges(
    mesh: Any,
    feature_angle_deg: float = 30.0,
    max_edges: int = 8000,
    sample_rate: float = 1.0,
    include_boundary: bool = True,
    rng_seed: int = 1234,
) -> NDArrayInt:
    """Extract an edge list suitable for a 'wireframe' outline look.

    Strategy:
    - crease edges (dihedral angle > feature threshold)
    - boundary edges (edges used by only 1 face), if requested
    - deterministic downsample to max_edges

    Returns
    -------
    edges: (M,2) int32
    """
    require_trimesh()  # ensures trimesh import
    if not hasattr(mesh, "faces") or mesh.faces is None:
        raise ValueError("mesh must have faces")

    # Ensure adjacency is computed
    # face_adjacency_edges: (K,2) edges between adjacent faces
    # face_adjacency_angles: (K,) dihedral angles in radians
    try:
        adj_edges = mesh.face_adjacency_edges
        adj_angles = mesh.face_adjacency_angles
    except Exception:
        # Force compute
        _ = mesh.face_adjacency
        adj_edges = mesh.face_adjacency_edges
        adj_angles = mesh.face_adjacency_angles

    # Feature edges by dihedral angle
    angle_rad = np.deg2rad(float(feature_angle_deg))
    feat_mask = adj_angles > angle_rad
    feat_edges = adj_edges[feat_mask] if len(adj_edges) else np.zeros((0, 2), dtype=np.int64)

    edges = feat_edges

    if include_boundary:
        # boundary edges are those which appear only once in mesh edges
        # Use mesh.edges_unique and mesh.edges_unique_inverse to count
        unique = mesh.edges_unique
        inv = mesh.edges_unique_inverse
        # Count occurrences
        counts = np.bincount(inv, minlength=len(unique))
        boundary = unique[counts == 1] if len(unique) else np.zeros((0, 2), dtype=np.int64)
        edges = np.vstack([edges, boundary]) if len(edges) or len(boundary) else np.zeros((0, 2), dtype=np.int64)

    if len(edges) == 0:
        return np.zeros((0, 2), dtype=np.int32)

    # Normalize edge ordering (a<b) and dedupe
    a = np.minimum(edges[:, 0], edges[:, 1])
    b = np.maximum(edges[:, 0], edges[:, 1])
    edges = np.stack([a, b], axis=1)
    edges = np.unique(edges, axis=0)

    # Deterministic sample
    if sample_rate < 1.0 and len(edges) > 0:
        rng = np.random.default_rng(int(rng_seed))
        keep = rng.random(len(edges)) < float(sample_rate)
        edges = edges[keep]

    if max_edges and len(edges) > int(max_edges):
        rng = np.random.default_rng(int(rng_seed))
        idx = rng.choice(len(edges), size=int(max_edges), replace=False)
        edges = edges[idx]

    return edges.astype(np.int32)


def generate_rib_edges(
    mesh: Any,
    axis: int = 0,
    slices: int = 8,
    thickness_frac: float = 0.03,
    rng_seed: int = 1234,
    max_edges: int = 1500,
) -> NDArrayInt:
    """Generate synthetic 'rib' edges to create internal structure hints.

    This is a stylistic tool: it does not try to be an engineering-accurate frame.

    Method:
    - take slices along the chosen axis (default X)
    - find extreme vertices in other axes within each slice
    - connect those extremes into a simple diamond loop

    Returns
    -------
    edges: (M,2) int32, referencing existing mesh vertices
    """
    v = np.asarray(mesh.vertices, dtype=np.float64)
    if v.shape[0] < 8 or slices <= 0:
        return np.zeros((0, 2), dtype=np.int32)

    ax = int(axis) % 3
    other = [i for i in range(3) if i != ax]
    mn = float(v[:, ax].min())
    mx = float(v[:, ax].max())
    span = mx - mn
    if span <= 1e-9:
        return np.zeros((0, 2), dtype=np.int32)

    thick = float(thickness_frac) * span
    # slice positions avoid the extreme ends
    positions = np.linspace(mn + span * 0.1, mx - span * 0.1, int(slices))

    edges_out: list[tuple[int, int]] = []
    rng = np.random.default_rng(int(rng_seed))

    for s in positions:
        mask = np.abs(v[:, ax] - s) <= thick
        idx = np.nonzero(mask)[0]
        if len(idx) < 12:
            continue

        pts = v[idx]

        # Extreme indices along the other axes
        ymin_i = idx[int(np.argmin(pts[:, other[0]]))]
        ymax_i = idx[int(np.argmax(pts[:, other[0]]))]
        zmin_i = idx[int(np.argmin(pts[:, other[1]]))]
        zmax_i = idx[int(np.argmax(pts[:, other[1]]))]

        ring = [ymin_i, zmax_i, ymax_i, zmin_i]
        for a, b in zip(ring, ring[1:] + ring[:1]):
            if a != b:
                edges_out.append((int(a), int(b)))

    if not edges_out:
        return np.zeros((0, 2), dtype=np.int32)

    edges = np.asarray(edges_out, dtype=np.int32)

    # Dedupe
    a = np.minimum(edges[:, 0], edges[:, 1])
    b = np.maximum(edges[:, 0], edges[:, 1])
    edges = np.stack([a, b], axis=1)
    edges = np.unique(edges, axis=0)

    if max_edges and len(edges) > int(max_edges):
        idx = rng.choice(len(edges), size=int(max_edges), replace=False)
        edges = edges[idx]

    return edges.astype(np.int32)


def extract_lod_edge_sets(
    mesh: Any,
    lods: Tuple[LODSpec, ...],
    rng_seed: int = 1234,
) -> Dict[str, NDArrayInt]:
    """Extract multiple LOD edge sets from a mesh."""
    out: Dict[str, NDArrayInt] = {}
    for i, spec in enumerate(lods):
        edges = extract_wireframe_edges(
            mesh,
            feature_angle_deg=spec.feature_angle_deg,
            max_edges=spec.max_edges,
            sample_rate=spec.sample_rate,
            include_boundary=spec.include_boundary,
            rng_seed=rng_seed + i * 17,
        )
        if spec.include_ribs and spec.ribs_slices > 0:
            ribs = generate_rib_edges(
                mesh,
                axis=0,
                slices=spec.ribs_slices,
                thickness_frac=0.03,
                rng_seed=rng_seed + i * 17 + 9,
                max_edges=max(200, int(spec.max_edges * 0.25)),
            )
            if len(ribs):
                edges = np.vstack([edges, ribs])
                # Dedupe again
                a = np.minimum(edges[:, 0], edges[:, 1])
                b = np.maximum(edges[:, 0], edges[:, 1])
                edges = np.stack([a, b], axis=1)
                edges = np.unique(edges, axis=0).astype(np.int32)

                if spec.max_edges and len(edges) > int(spec.max_edges):
                    rng = np.random.default_rng(int(rng_seed + i * 17 + 33))
                    idx = rng.choice(len(edges), size=int(spec.max_edges), replace=False)
                    edges = edges[idx]

        out[spec.name] = edges.astype(np.int32)
    return out
