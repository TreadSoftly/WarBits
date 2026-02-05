from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np
import numpy.typing as npt

from .anchors import AnchorDB, AnchorMap, compute_default_anchors, merge_anchor_maps
from .blueprint_db import BlueprintDB
from .blueprint_schema import Blueprint
from .lod import LODPolicy

NDArrayF = npt.NDArray[np.float64]
NDArrayI = npt.NDArray[np.int32]


@dataclass
class CachedGeometry:
    blueprint_id: str
    kind: Optional[str]
    vertices_m: NDArrayF  # (N,3) float64
    edges_by_lod: Dict[str, NDArrayI]  # lod_name -> (M,2) int32
    bounds_min_m: NDArrayF
    bounds_max_m: NDArrayF
    dims_m: NDArrayF
    center_m: NDArrayF
    anchors: Optional[AnchorMap] = None  # lazily computed/merged

    @property
    def verts(self) -> NDArrayF:
        return self.vertices_m


class VisualRegistry:
    """Runtime access to visual blueprints.

    The registry:
    - loads one or more BlueprintDBs
    - caches numpy representations for fast renderer consumption
    - selects LOD deterministically using LODPolicy

    It does **not** import matplotlib or panda3d.
    """

    def __init__(
        self,
        db: BlueprintDB,
        lod_policy: Optional[LODPolicy] = None,
        anchor_db: Optional[AnchorDB] = None,
    ) -> None:
        self._db = db
        self._lod_policy = lod_policy or LODPolicy()
        self._anchor_db = anchor_db
        self._cache: Dict[str, CachedGeometry] = {}

    @staticmethod
    def load(
        db_paths: Sequence[str | Path],
        *,
        lod_policy: Optional[LODPolicy] = None,
        anchor_db: Optional[AnchorDB] = None,
    ) -> "VisualRegistry":
        db = BlueprintDB.load_many_jsonl(db_paths)
        return VisualRegistry(db=db, lod_policy=lod_policy, anchor_db=anchor_db)

    @classmethod
    def from_files(
        cls,
        blueprint_jsonl_path: str | Path,
        *,
        lod_policy: Optional[LODPolicy] = None,
        anchors_jsonl_path: Optional[str | Path] = None,
    ) -> "VisualRegistry":
        db = BlueprintDB.load_jsonl(blueprint_jsonl_path)
        anchor_db = AnchorDB.load_jsonl(anchors_jsonl_path) if anchors_jsonl_path else None
        return cls(db=db, lod_policy=lod_policy, anchor_db=anchor_db)

    @property
    def lod_policy(self) -> LODPolicy:
        """Expose the active LODPolicy (compatibility with older call sites)."""
        return self._lod_policy

    # ------------------------------------------------------------------
    # Blueprint access
    # ------------------------------------------------------------------
    def get(self, blueprint_id: str) -> Optional[Blueprint]:
        return self._db.get(blueprint_id)

    def require(self, blueprint_id: str) -> Blueprint:
        return self._db.require(blueprint_id)

    def ids(self) -> Tuple[str, ...]:
        return self._db.ids()

    def available_blueprint_ids(self) -> List[str]:
        return sorted(self._db.ids())

    # ------------------------------------------------------------------
    # Geometry (cached numpy)
    # ------------------------------------------------------------------
    def geometry(self, blueprint_id: str) -> Optional[CachedGeometry]:
        if blueprint_id in self._cache:
            return self._cache[blueprint_id]

        bp = self.get(blueprint_id)
        if bp is None:
            return None

        if bp.repr != "wire3d":
            return None

        v: NDArrayF = np.asarray(bp.vertices_m, dtype=np.float64)
        edges_by_lod: Dict[str, NDArrayI] = {}
        for lod_name, edges in bp.edges_by_lod.items():
            edges_by_lod[lod_name] = np.asarray(edges, dtype=np.int32)

        if not edges_by_lod:
            return None

        vmin = v.min(axis=0)
        vmax = v.max(axis=0)
        dims = vmax - vmin
        center = 0.5 * (vmin + vmax)

        cached = CachedGeometry(
            blueprint_id=bp.blueprint_id,
            kind=bp.kind or None,
            vertices_m=v,
            edges_by_lod=edges_by_lod,
            bounds_min_m=vmin,
            bounds_max_m=vmax,
            dims_m=dims,
            center_m=center,
            anchors=None,
        )
        self._cache[blueprint_id] = cached
        return cached

    def get_cached(self, blueprint_id: str) -> CachedGeometry:
        geom = self.geometry(blueprint_id)
        if geom is None:
            raise KeyError(f"Blueprint not found or unsupported: {blueprint_id}")
        return geom

    def get_geometry(
        self,
        blueprint_id: str,
        *,
        distance_m: Optional[float] = None,
    ) -> Tuple[NDArrayF, NDArrayI]:
        """Return (vertices, edges) with LOD chosen from distance_m."""
        geom = self.get_cached(blueprint_id)
        lod_name = self.pick_lod_name(blueprint_id, float(distance_m or 0.0))
        edges = geom.edges_by_lod.get(lod_name or "", None)
        if edges is None:
            edges = geom.edges_by_lod.get("lod0") or geom.edges_by_lod.get("base")
        if edges is None:
            raise ValueError(f"Blueprint {blueprint_id} has no edges")
        return geom.vertices_m, edges

    def pick_lod_name(self, blueprint_id: str, distance_m: float) -> Optional[str]:
        bp = self.get(blueprint_id)
        if bp is None or bp.repr != "wire3d":
            return None
        lod = self._lod_policy.select_lod(distance_m=distance_m)
        if lod and lod in bp.lod_edges:
            return lod
        # If chosen LOD isn't present, fall back gracefully:
        # - prefer lod0 if exists
        if "lod0" in bp.lod_edges:
            return "lod0"
        return None

    def edges_for_distance(self, blueprint_id: str, distance_m: float) -> Optional[NDArrayI]:
        geom = self.geometry(blueprint_id)
        if geom is None:
            return None
        lod = self.pick_lod_name(blueprint_id, distance_m)
        if lod and lod in geom.edges_by_lod:
            return geom.edges_by_lod[lod]
        return geom.edges_by_lod["base"]

    def get_bounds(self, blueprint_id: str) -> Tuple[NDArrayF, NDArrayF]:
        geom = self.get_cached(blueprint_id)
        return geom.bounds_min_m.copy(), geom.bounds_max_m.copy()

    def get_dims(self, blueprint_id: str) -> NDArrayF:
        geom = self.get_cached(blueprint_id)
        return geom.dims_m.copy()

    def get_center(self, blueprint_id: str) -> NDArrayF:
        geom = self.get_cached(blueprint_id)
        return geom.center_m.copy()

    def get_anchors(self, blueprint_id: str) -> AnchorMap:
        geom = self.get_cached(blueprint_id)
        if geom.anchors is not None:
            return {k: v.copy() for k, v in geom.anchors.items()}

        bp = self.require(blueprint_id)
        rec = self._anchor_db.get(blueprint_id) if self._anchor_db else None

        base = compute_default_anchors(
            blueprint_id=blueprint_id,
            vertices_m=geom.vertices_m,
            kind_hint=rec.kind_hint if rec else None,
            meta_kind=bp.kind or None,
        )

        if bp.anchors:
            base = merge_anchor_maps(
                base,
                {k: np.asarray(v, dtype=np.float64) for k, v in bp.anchors.items()},
            )
        if rec is not None:
            base = merge_anchor_maps(base, rec.anchors)

        geom.anchors = base
        return {k: v.copy() for k, v in base.items()}


# Backwards/ergonomic alias
BlueprintRegistry = VisualRegistry
BlueprintRegistry = VisualRegistry
