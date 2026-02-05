from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional, Sequence, Tuple, TypeAlias

import numpy as np
from numpy.typing import NDArray

from warbits.visual.blueprint_db import BlueprintDB
from warbits.visual.blueprint_schema import Blueprint
from warbits.visual.lod import LODPolicy

FloatArray: TypeAlias = NDArray[np.float64]
IntArray: TypeAlias = NDArray[np.int32]


@dataclass
class CachedGeometry:
    blueprint_id: str
    vertices_m: FloatArray  # (N,3) float64
    edges_by_lod: Dict[str, IntArray]  # lod_name -> (M,2) int32


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
    ) -> None:
        self._db = db
        self._lod_policy = lod_policy or LODPolicy()
        self._cache: Dict[str, CachedGeometry] = {}

    @staticmethod
    def load(db_paths: Sequence[str | Path], lod_policy: Optional[LODPolicy] = None) -> "VisualRegistry":
        db = BlueprintDB.load_many_jsonl(db_paths)
        return VisualRegistry(db=db, lod_policy=lod_policy)

    # ------------------------------------------------------------------
    # Blueprint access
    # ------------------------------------------------------------------
    def get(self, blueprint_id: str) -> Optional[Blueprint]:
        return self._db.get(blueprint_id)

    def require(self, blueprint_id: str) -> Blueprint:
        return self._db.require(blueprint_id)

    def ids(self) -> Tuple[str, ...]:
        return self._db.ids()

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
            # For now only wire3d has fast segment geometry
            return None

        # Build numpy cache
        v = np.asarray(bp.vertices_m, dtype=np.float64)
        edges_by_lod: Dict[str, IntArray] = {}

        # base edges treated as lod0 if not present
        edges_by_lod["base"] = np.asarray(bp.edges, dtype=np.int32)
        for lod_name, edges in bp.lod_edges.items():
            edges_by_lod[lod_name] = np.asarray(edges, dtype=np.int32)

        cached = CachedGeometry(blueprint_id=bp.blueprint_id, vertices_m=v, edges_by_lod=edges_by_lod)
        self._cache[blueprint_id] = cached
        return cached

    def pick_lod_name(self, blueprint_id: str, distance_m: float) -> Optional[str]:
        bp = self.get(blueprint_id)
        if bp is None or bp.repr != "wire3d":
            return None
        lod = self._lod_policy.pick(distance_m)
        if lod and lod in bp.lod_edges:
            return lod
        # If chosen LOD isn't present, fall back gracefully:
        # - prefer lod0 if exists
        if "lod0" in bp.lod_edges:
            return "lod0"
        return None

    def edges_for_distance(self, blueprint_id: str, distance_m: float) -> Optional[IntArray]:
        geom = self.geometry(blueprint_id)
        if geom is None:
            return None
        lod = self.pick_lod_name(blueprint_id, distance_m)
        if lod and lod in geom.edges_by_lod:
            return geom.edges_by_lod[lod]
        return geom.edges_by_lod["base"]

    @property
    def lod_policy(self) -> LODPolicy:
        """Expose the active LODPolicy (compatibility with older call sites)."""
        return self._lod_policy


# Backwards/ergonomic alias
BlueprintRegistry = VisualRegistry
