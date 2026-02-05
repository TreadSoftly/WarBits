from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
from numpy.typing import NDArray

from warbits.visual.anchors import AnchorDB, AnchorMap, compute_default_anchors, merge_anchor_maps
from warbits.visual.blueprint_db import BlueprintDB
from warbits.visual.lod import LODPolicy


@dataclass
class CachedGeometry:
    blueprint_id: str
    meta_kind: Optional[str]
    vertices_m: NDArray[np.float_]
    edges_by_lod: Dict[str, NDArray[np.int_]]

    bounds_min_m: NDArray[np.float_]
    bounds_max_m: NDArray[np.float_]
    dims_m: NDArray[np.float_]
    center_m: NDArray[np.float_]

    anchors: Optional[AnchorMap] = None  # lazily computed/merged


class VisualRegistry:
    """
    Registry / cache for visual blueprints:
    - loads Blueprint records from BlueprintDB
    - caches numpy representations for fast renderer consumption
    - selects LOD deterministically using LODPolicy
    - optionally merges in anchor overrides from AnchorDB

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

    def available_blueprint_ids(self) -> List[str]:
        return sorted(self._db.ids())

    def get_cached(self, blueprint_id: str) -> CachedGeometry:
        if blueprint_id in self._cache:
            return self._cache[blueprint_id]

        bp = self._db.get(blueprint_id)
        if bp is None:
            raise KeyError(f"Unknown blueprint_id: {blueprint_id}")

        V = np.asarray(bp.vertices_m, dtype=np.float32)

        edges_by_lod: Dict[str, NDArray[np.int_]] = {}
        for lod_key, edges in bp.edges_by_lod.items():
            edges_by_lod[lod_key] = np.asarray(edges, dtype=np.int32)

        # Bounds
        vmin = V.min(axis=0)
        vmax = V.max(axis=0)
        dims = vmax - vmin
        center = 0.5 * (vmin + vmax)

        meta_kind = getattr(bp.meta, "kind", None)

        cg = CachedGeometry(
            blueprint_id=blueprint_id,
            meta_kind=meta_kind,
            vertices_m=V,
            edges_by_lod=edges_by_lod,
            bounds_min_m=vmin,
            bounds_max_m=vmax,
            dims_m=dims,
            center_m=center,
            anchors=None,
        )
        self._cache[blueprint_id] = cg
        return cg

    def get_geometry(
        self,
        blueprint_id: str,
        *,
        distance_m: Optional[float] = None,
    ) -> Tuple[NDArray[np.float_], NDArray[np.int_]]:
        """
        Returns (vertices_m, edges) with an LOD chosen from distance_m.
        """
        cg = self.get_cached(blueprint_id)

        lod_key = self._lod_policy.select_lod(distance_m=distance_m)
        edges = cg.edges_by_lod.get(lod_key or "")
        if edges is None:
            # If chosen LOD isn't present, fall back gracefully:
            edges = cg.edges_by_lod.get("lod0") or cg.edges_by_lod.get("base")
            if edges is None:
                # No edges at all is possible (bad data), but keep failure explicit.
                raise ValueError(f"Blueprint {blueprint_id} has no edges_by_lod")

        return cg.vertices_m, edges

    def get_bounds(self, blueprint_id: str) -> Tuple[NDArray[np.float_], NDArray[np.float_]]:
        cg = self.get_cached(blueprint_id)
        return cg.bounds_min_m.copy(), cg.bounds_max_m.copy()

    def get_dims(self, blueprint_id: str) -> NDArray[np.float_]:
        cg = self.get_cached(blueprint_id)
        return cg.dims_m.copy()

    def get_center(self, blueprint_id: str) -> NDArray[np.float_]:
        cg = self.get_cached(blueprint_id)
        return cg.center_m.copy()

    def get_anchors(self, blueprint_id: str) -> AnchorMap:
        """
        Returns merged anchor set (defaults + overrides).
        Cached after first call.
        """
        cg = self.get_cached(blueprint_id)
        if cg.anchors is not None:
            return {k: v.copy() for k, v in cg.anchors.items()}

        rec = self._anchor_db.get(blueprint_id) if self._anchor_db else None
        kind_hint = rec.kind_hint if rec else None

        defaults = compute_default_anchors(
            blueprint_id=blueprint_id,
            vertices_m=cg.vertices_m,
            kind_hint=kind_hint,
            meta_kind=cg.meta_kind,
        )

        if rec is None:
            merged = defaults
        else:
            merged = merge_anchor_maps(defaults, rec.anchors)

        cg.anchors = merged
        return {k: v.copy() for k, v in merged.items()}

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
        return cls(db=db, lod_policy=lod_policy, anchor_db=anchor_db)
