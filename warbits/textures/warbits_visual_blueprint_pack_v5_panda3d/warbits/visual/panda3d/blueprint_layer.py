from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, Tuple

import numpy as np
from numpy.typing import NDArray

# Runtime registry from previous packs
from warbits.visual.registry import VisualRegistry

from .line_batch import DynamicLineBatch
from .style import NEON_GREEN, WireframeP3DStyle

NDArrayFloat = NDArray[np.float32]


# ---------------------------------------------------------------------------
# Coordinate mapping
# ---------------------------------------------------------------------------
# Assumption: sim/model coordinates are:
#   X = forward
#   Y = left
#   Z = up
#
# Panda3D default is:
#   X = right
#   Y = forward
#   Z = up
#
# Therefore:
#   panda_x = -sim_y
#   panda_y =  sim_x
#   panda_z =  sim_z
#
SIM_TO_P3D = np.array(
    [
        [0.0, -1.0, 0.0],  # panda_x = -sim_y
        [1.0, 0.0, 0.0],  # panda_y =  sim_x
        [0.0, 0.0, 1.0],  # panda_z =  sim_z
    ],
    dtype=np.float32,
)


def sim_to_p3d_points(points_sim: NDArrayFloat) -> NDArrayFloat:
    """Map Nx3 points from sim coordinates to Panda3D coordinates."""
    pts = np.asarray(points_sim, dtype=np.float32)
    if pts.ndim != 2 or pts.shape[1] != 3:
        raise ValueError(f"points_sim must be Nx3. Got {pts.shape}")
    return pts @ SIM_TO_P3D.T


def sim_to_p3d_vec(vec_sim: NDArrayFloat) -> NDArrayFloat:
    v = np.asarray(vec_sim, dtype=np.float32).reshape(1, 3)
    return (v @ SIM_TO_P3D.T).reshape(3)


# ---------------------------------------------------------------------------
# Public API: instances
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class BlueprintInstance:
    blueprint_id: str
    position_m: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    rotation_m: Tuple[Tuple[float, float, float], Tuple[float, float, float], Tuple[float, float, float]] = (
        (1.0, 0.0, 0.0),
        (0.0, 1.0, 0.0),
        (0.0, 0.0, 1.0),
    )
    scale: float = 1.0


# ---------------------------------------------------------------------------
# Layer: batch blueprints into one dynamic line batch
# ---------------------------------------------------------------------------


class BlueprintP3DLayer:
    """Render wireframe blueprints in Panda3D using a single dynamic line batch.

    You give it:
    - a VisualRegistry (blueprint DB + LOD policy)
    - a list of BlueprintInstance (id + pose)
    - a camera position (for LOD selection)

    It outputs:
    - a Panda3D NodePath you attach to render.
    """

    def __init__(self, registry: VisualRegistry, *, max_segments: int = 50_000, style: WireframeP3DStyle = NEON_GREEN):
        self.registry = registry
        self.batch = DynamicLineBatch(max_segments=max_segments, style=style, name="blueprint_world_lines")
        self.nodepath = self.batch.nodepath

        # Cache: (blueprint_id, lod_name) -> flat local endpoints shaped (E*2,3)
        self._flat_cache: Dict[Tuple[str, str], NDArrayFloat] = {}

    def _flat_local(self, blueprint_id: str, lod_name: str) -> NDArrayFloat:
        key = (blueprint_id, lod_name)
        hit = self._flat_cache.get(key)
        if hit is not None:
            return hit

        geom = self.registry.geometry(blueprint_id)
        if geom is None:
            empty = np.zeros((0, 3), dtype=np.float32)
            self._flat_cache[key] = empty
            return empty

        edges = geom.edges_by_lod.get(lod_name) or geom.edges_by_lod.get("base")
        if edges is None:
            empty = np.zeros((0, 3), dtype=np.float32)
            self._flat_cache[key] = empty
            return empty

        verts = geom.vertices_m.astype(np.float32, copy=False)  # (V,3)
        idx = edges.reshape(-1)  # (E*2,)
        flat = verts[idx]  # (E*2,3)

        # Store a copy so we own the memory (registry may hand out views)
        flat = np.array(flat, dtype=np.float32, copy=True)
        self._flat_cache[key] = flat
        return flat

    def render(self, *, camera_pos_m: Tuple[float, float, float], instances: Iterable[BlueprintInstance]) -> None:
        """Build the world line batch for this frame."""
        cam = np.asarray(camera_pos_m, dtype=np.float32).reshape(3)

        buf = self.batch.begin()
        cursor = 0  # vertex cursor (each segment consumes 2 vertices)

        for inst in instances:
            pos = np.asarray(inst.position_m, dtype=np.float32).reshape(3)
            rot = np.asarray(inst.rotation_m, dtype=np.float32).reshape(3, 3)

            dist = float(np.linalg.norm(pos - cam))
            lod = self.registry.pick_lod_name(inst.blueprint_id, dist) or "lod0"

            flat_local = self._flat_local(inst.blueprint_id, lod)
            nverts = int(flat_local.shape[0])
            if cursor + nverts > buf.shape[0]:
                # Not enough space; stop adding more.
                break

            # Combined transform:
            #   p_world_sim = p_local @ rot.T + pos
            #   p_world_p3d = p_world_sim @ SIM_TO_P3D.T
            #
            # => p_world_p3d = p_local @ ( (SIM_TO_P3D @ rot).T ) + (pos @ SIM_TO_P3D.T)
            #
            mat = (SIM_TO_P3D @ rot).T  # (3,3)
            out = buf[cursor : cursor + nverts]  # view into staging buffer

            np.matmul(flat_local, mat, out=out)
            if inst.scale != 1.0:
                out *= float(inst.scale)
            out += pos @ SIM_TO_P3D.T

            cursor += nverts

        active_segments = cursor // 2
        self.batch.commit(active_segments=active_segments)
