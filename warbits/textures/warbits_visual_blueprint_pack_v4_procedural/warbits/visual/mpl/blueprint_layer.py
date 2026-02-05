from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence, Tuple, cast

import numpy as np
from mpl_toolkits.mplot3d.art3d import Line3DCollection  # type: ignore[import-not-found]
from numpy.typing import NDArray

from warbits.visual.lod import LODPolicy
from warbits.visual.mpl.style import WireframeStyle, neon_green_style

NDArrayFloat = NDArray[np.float64]
NDArrayInt = NDArray[np.int32]
RGBA = Tuple[float, float, float, float]


def rot_from_yaw_pitch_roll(yaw: float, pitch: float, roll: float) -> NDArrayFloat:
    """Return a 3x3 rotation matrix from yaw/pitch/roll (radians).

    Convention:
    - yaw about +Z
    - pitch about +Y
    - roll about +X

    This is a common aerospace convention when using:
    x forward, y left, z up.

    If your sim uses a different convention, supply your own 3x3 matrix directly.
    """
    cy, sy = np.cos(yaw), np.sin(yaw)
    cp, sp = np.cos(pitch), np.sin(pitch)
    cr, sr = np.cos(roll), np.sin(roll)

    Rz = np.array(
        [[cy, -sy, 0.0], [sy, cy, 0.0], [0.0, 0.0, 1.0]],
        dtype=float,
    )
    Ry = np.array(
        [[cp, 0.0, sp], [0.0, 1.0, 0.0], [-sp, 0.0, cp]],
        dtype=float,
    )
    Rx = np.array(
        [[1.0, 0.0, 0.0], [0.0, cr, -sr], [0.0, sr, cr]],
        dtype=float,
    )
    return (Rz @ Ry @ Rx).astype(float)


@dataclass(frozen=True)
class BlueprintInstance:
    """A single drawable instance of a Visual Blueprint."""

    blueprint_id: str

    # world transform
    position_m: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    rotation_mat: Optional[NDArrayFloat] = None  # (3,3) world-from-local
    scale: float = 1.0

    # semantic style
    role: str = "neutral"  # friendly / hostile / neutral / projectile / etc.

    # Optional: override chosen LOD name; if None, LODPolicy decides
    lod_override: Optional[str] = None

    def R(self) -> NDArrayFloat:
        if self.rotation_mat is None:
            return np.eye(3, dtype=float)
        r = np.asarray(self.rotation_mat, dtype=float)
        if r.shape != (3, 3):
            raise ValueError(f"rotation_mat must be (3,3), got {r.shape}")
        return r


class _SegmentBuffer:
    """Reusable numpy buffer to reduce per-frame allocations."""

    def __init__(self) -> None:
        self._buf: Optional[NDArrayFloat] = None

    def ensure(self, n: int) -> NDArrayFloat:
        if n <= 0:
            self._buf = np.empty((0, 2, 3), dtype=float)
            return self._buf
        if self._buf is None or self._buf.shape[0] < n:
            # grow with slack to reduce churn
            grow = int(max(64, n * 1.25))
            self._buf = np.empty((grow, 2, 3), dtype=float)
        return self._buf[:n]


class MPLBlueprintLayer:
    """Batched Matplotlib renderer for Visual Blueprints.

    Why this exists:
    - Matplotlib becomes a slideshow if you create one artist per unit per frame.
    - This layer batches instances into a small number of Line3DCollections
      (by role + pass), and updates their segments each frame.

    Draw passes:
    - outline (base edges, always)
    - outline glow (optional)
    - detail (optional, distance-based LOD edges)

    Basic usage:

        from warbits.visual.blueprint_db import BlueprintDB
        from warbits.visual.registry import VisualRegistry
        from warbits.visual.mpl.blueprint_layer import MPLBlueprintLayer

        db = BlueprintDB.load_jsonl("data/visual_blueprints.jsonl")
        registry = VisualRegistry(db)
        layer = MPLBlueprintLayer(ax, registry)

        # per frame:
        layer.update(instances, camera_pos=(...))
    """

    def __init__(
        self,
        ax: Any,
        registry: Any,
        *,
        style: Optional[WireframeStyle] = None,
        lod_policy: Optional[LODPolicy] = None,
        pixel_mode: bool = False,
        enable_detail: bool = True,
    ) -> None:
        self.ax = ax
        self.registry: Any = registry
        self.style: WireframeStyle = style if style is not None else neon_green_style()
        self.lod_policy = lod_policy if lod_policy is not None else registry.lod_policy
        self.pixel_mode = bool(pixel_mode)
        self.enable_detail = bool(enable_detail)

        # Artists: role -> dict(pass_name -> Line3DCollection)
        self._artists: Dict[str, Dict[str, Line3DCollection]] = {}

        # Buffers: role -> pass -> SegmentBuffer
        self._buffers: Dict[str, Dict[str, _SegmentBuffer]] = {}

    def _get_artist(self, role: str, pass_name: str, *, rgba: RGBA, lw: float, alpha: float) -> Line3DCollection:
        role_key = (role or "neutral").lower()
        if role_key not in self._artists:
            self._artists[role_key] = {}
            self._buffers[role_key] = {}
        if pass_name in self._artists[role_key]:
            return self._artists[role_key][pass_name]

        # Create artist once, then mutate segments each frame.
        lc = Line3DCollection([], linewidths=lw, colors=[rgba], alpha=alpha)
        self.ax.add_collection3d(lc)
        self._artists[role_key][pass_name] = lc
        self._buffers[role_key][pass_name] = _SegmentBuffer()
        return lc

    def clear(self) -> None:
        """Remove all artists from the axes."""
        for role_map in self._artists.values():
            for lc in role_map.values():
                try:
                    lc.remove()
                except Exception:
                    pass
        self._artists.clear()
        self._buffers.clear()

    def update(
        self,
        instances: Sequence[BlueprintInstance],
        *,
        camera_pos: Tuple[float, float, float] = (0.0, 0.0, 0.0),
    ) -> None:
        """Update artists for a new frame (in-place)."""
        cam = np.asarray(camera_pos, dtype=float).reshape(3)

        # Group instances by role so we can batch each role to one artist per pass.
        by_role: Dict[str, List[BlueprintInstance]] = {}
        for inst in instances:
            role_key = (inst.role or "neutral").lower()
            by_role.setdefault(role_key, []).append(inst)

        # For roles that disappeared this frame, keep artists but clear their segments.
        roles_all = set(self._artists.keys()) | set(by_role.keys())

        for role in sorted(roles_all):
            inst_list = by_role.get(role, [])

            # Outline segments (base edges) for all instances in this role.
            outline_segments = self._build_segments(inst_list, cam, detail=False)
            self._sync_pass(role, "outline", outline_segments, detail=False, glow=False)

            # Optional glow: same outline segments, thicker/softer
            if self.style.glow_enabled:
                self._sync_pass(role, "glow", outline_segments, detail=False, glow=True)
            else:
                self._sync_pass(role, "glow", np.empty((0, 2, 3), dtype=float), detail=False, glow=True)

            # Optional detail pass: distance-based LOD edges
            if self.enable_detail:
                detail_segments = self._build_segments(inst_list, cam, detail=True)
                self._sync_pass(role, "detail", detail_segments, detail=True, glow=False)
            else:
                self._sync_pass(role, "detail", np.empty((0, 2, 3), dtype=float), detail=True, glow=False)

    def _sync_pass(self, role: str, pass_name: str, segments: NDArrayFloat, *, detail: bool, glow: bool) -> None:
        # Choose distance proxy for fade: estimate from first segment midpoint
        if segments.shape[0] > 0:
            mid = 0.5 * (segments[0, 0] + segments[0, 1])
            d = float(np.linalg.norm(mid))
        else:
            d = 0.0

        rgba, lw, alpha, allow_glow = self.style.resolve_pass(role, d, pixel_mode=self.pixel_mode, detail=detail)

        if glow:
            if not allow_glow:
                segments = np.empty((0, 2, 3), dtype=float)
            lw = lw * float(self.style.glow_lw_multiplier)
            alpha = alpha * float(self.style.glow_alpha_multiplier)
            rgba = (rgba[0], rgba[1], rgba[2], alpha)

        lc = self._get_artist(role, pass_name, rgba=rgba, lw=lw, alpha=alpha)
        lc.set_linewidth(lw)
        lc.set_color([rgba])
        lc.set_alpha(alpha)
        lc.set_segments(segments.tolist())

    def _build_segments(
        self, instances: Sequence[BlueprintInstance], cam: NDArrayFloat, *, detail: bool
    ) -> NDArrayFloat:
        if not instances:
            return np.empty((0, 2, 3), dtype=float)

        # 1) Count edges to allocate one big segments array.
        total_edges = 0
        geom_cache: list[tuple[BlueprintInstance, Any, NDArrayInt]] = []
        for inst in instances:
            try:
                geom = self.registry.geometry(inst.blueprint_id)
            except KeyError:
                continue

            if geom is None:
                continue

            pos = np.asarray(inst.position_m, dtype=float).reshape(3)
            dist = float(np.linalg.norm(pos - cam))

            if detail:
                lod_name = inst.lod_override or self.lod_policy.pick(dist)
                edges = geom.edges_by_lod.get(lod_name, None)
                if edges is None or edges.size == 0:
                    continue
            else:
                edges = geom.edges_by_lod.get("base")

            if edges is None or edges.size == 0:
                continue

            edges = cast(NDArrayInt, edges)
            total_edges += int(edges.shape[0])
            geom_cache.append((inst, geom, edges))

        if total_edges == 0:
            return np.empty((0, 2, 3), dtype=float)

        # 2) Fill segments
        segments = np.empty((total_edges, 2, 3), dtype=float)
        offset = 0

        for inst, geom, edges in geom_cache:
            V = cast(NDArrayFloat, geom.vertices_m)  # (N,3)
            pos = np.asarray(inst.position_m, dtype=float).reshape(3)
            R = inst.R()
            s = float(inst.scale)

            # Transform: world = (local * scale) @ R^T + pos
            Vw = (V * s) @ R.T
            Vw += pos

            a = edges[:, 0]
            b = edges[:, 1]
            n = int(edges.shape[0])

            segments[offset : offset + n, 0, :] = Vw[a]
            segments[offset : offset + n, 1, :] = Vw[b]
            offset += n

        return segments[:offset]
        return segments[:offset]
