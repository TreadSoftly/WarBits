from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np

from .bursts import BurstParams, BurstPool
from .config import FxConfig
from .explosions import ExplosionParams, ExplosionPool
from .trails import TrailParams, TrailRingBuffer
from .types import FxFrameData, FxLayerBatch


@dataclass(frozen=True)
class DefaultTrailFamilies:
    """Common trail family parameter presets."""

    tracers: TrailParams = TrailParams(max_objects=2048, history_len=4, fade_pow=1.2)
    contrails: TrailParams = TrailParams(max_objects=256, history_len=32, fade_pow=1.6)
    smoke: TrailParams = TrailParams(max_objects=512, history_len=24, fade_pow=1.8)


class FxManager:
    """High-performance FX builder that outputs line geometry batches.

    This is meant to sit between your simulation and your renderer.

    Minimal usage
    -------------
    ```py
    fx = FxManager(FxConfig())

    # each frame...
    fx.update_trail("tracers", bullet_ids, bullet_positions, frame_idx=frame)
    fx.update_trail("contrails", aircraft_ids, aircraft_positions, frame_idx=frame)
    fx.spawn_explosion(center_xyz, frame_idx=frame)

    frame_data = fx.build_frame(frame_idx=frame)
    renderer.update_fx(frame_data)
    ```

    Conventions
    -----------
    - Positions are XYZ in **meters** in world space.
    - The manager does not care what your coordinate system means; it just draws.
    """

    def __init__(
        self,
        cfg: FxConfig,
        *,
        trails: DefaultTrailFamilies = DefaultTrailFamilies(),
        explosion_params: Optional[ExplosionParams] = None,
        burst_params: Optional[BurstParams] = None,
    ) -> None:
        self.cfg = cfg

        self._trails: Dict[str, TrailRingBuffer] = {
            "tracers": TrailRingBuffer(trails.tracers),
            "contrails": TrailRingBuffer(trails.contrails),
            "smoke": TrailRingBuffer(trails.smoke),
        }

        self._explosions = ExplosionPool(explosion_params or ExplosionParams(
            max_explosions=cfg.max_explosions,
            lifetime_frames=cfg.explosion_life_frames,
            max_radius_m=cfg.explosion_max_radius_m,
        ))

        self._bursts = BurstPool(burst_params or BurstParams(
            max_bursts=cfg.max_impacts,
            lifetime_frames=cfg.impact_life_frames,
            max_radius_m=cfg.impact_max_radius_m,
        ))

    # --------------------
    # Trails
    # --------------------
    def update_trail(
        self,
        family: str,
        ids: np.ndarray,
        positions_xyz: np.ndarray,
        *,
        frame_idx: int,
    ) -> None:
        if family not in self._trails:
            raise KeyError(f"Unknown trail family: {family!r}. Known: {sorted(self._trails)}")
        self._trails[family].ingest(ids, positions_xyz, frame_idx=frame_idx)

    def clear_trail(self, family: str, *, frame_idx: int) -> None:
        if family not in self._trails:
            return
        self._trails[family].clear(frame_idx=frame_idx)

    # --------------------
    # Impulses
    # --------------------
    def spawn_explosion(
        self,
        center_xyz: np.ndarray,
        *,
        frame_idx: int,
        radius_m: Optional[float] = None,
        life_frames: Optional[int] = None,
    ) -> None:
        self._explosions.spawn(center_xyz, frame_idx=frame_idx, max_radius_m=radius_m, lifetime_frames=life_frames)

    def spawn_impact_burst(
        self,
        center_xyz: np.ndarray,
        *,
        frame_idx: int,
        normal_xyz: Optional[np.ndarray] = None,
        radius_m: Optional[float] = None,
        life_frames: Optional[int] = None,
    ) -> None:
        self._bursts.spawn(center_xyz, frame_idx=frame_idx, normal_xyz=normal_xyz, max_radius_m=radius_m, lifetime_frames=life_frames)

    # --------------------
    # Event ingestion (optional helper)
    # --------------------
    def ingest_event_dicts(self, events: Iterable[dict], *, frame_idx: int) -> None:
        """Best-effort helper to spawn FX from lightweight event dicts.

        Supported shapes (examples)
        ---------------------------
        - {"type": "explosion", "pos": [x,y,z], "radius": 50, "life": 25}
        - {"type": "impact", "pos": [x,y,z], "normal": [0,0,1]}

        Unknown events are ignored.
        """
        for e in events:
            et = (e.get("type") or e.get("kind") or "").lower()
            pos = e.get("pos") or e.get("position") or e.get("center")
            if pos is None:
                continue
            center = np.asarray(pos, dtype=np.float32)
            if center.shape != (3,):
                continue
            if et in {"explosion", "detonation", "blast"}:
                self.spawn_explosion(
                    center,
                    frame_idx=frame_idx,
                    radius_m=e.get("radius"),
                    life_frames=e.get("life"),
                )
            elif et in {"impact", "hit", "burst"}:
                normal = e.get("normal")
                n = np.asarray(normal, dtype=np.float32) if normal is not None else None
                self.spawn_impact_burst(
                    center,
                    frame_idx=frame_idx,
                    normal_xyz=n,
                    radius_m=e.get("radius"),
                    life_frames=e.get("life"),
                )

    # --------------------
    # Build frame
    # --------------------
    def build_frame(self, *, frame_idx: int) -> FxFrameData:
        """Return all FX layers for the current frame."""
        layers: Dict[str, FxLayerBatch] = {}

        # Trails
        tracer_segs, tracer_alpha = self._trails["tracers"].build_segments(frame_idx=frame_idx)
        if tracer_segs.shape[0] > self.cfg.max_tracer_segments:
            # Decimate deterministically: take every k-th segment.
            k = int(np.ceil(tracer_segs.shape[0] / self.cfg.max_tracer_segments))
            tracer_segs = tracer_segs[::k]
            tracer_alpha = tracer_alpha[::k]
        layers["tracers"] = FxLayerBatch(tracer_segs, tracer_alpha)

        contrail_segs, contrail_alpha = self._trails["contrails"].build_segments(frame_idx=frame_idx)
        if contrail_segs.shape[0] > self.cfg.max_contrail_segments:
            k = int(np.ceil(contrail_segs.shape[0] / self.cfg.max_contrail_segments))
            contrail_segs = contrail_segs[::k]
            contrail_alpha = contrail_alpha[::k]
        layers["contrails"] = FxLayerBatch(contrail_segs, contrail_alpha)

        smoke_segs, smoke_alpha = self._trails["smoke"].build_segments(frame_idx=frame_idx)
        if smoke_segs.shape[0] > self.cfg.max_smoke_segments:
            k = int(np.ceil(smoke_segs.shape[0] / self.cfg.max_smoke_segments))
            smoke_segs = smoke_segs[::k]
            smoke_alpha = smoke_alpha[::k]
        layers["smoke"] = FxLayerBatch(smoke_segs, smoke_alpha)

        # Impulses
        exp_segs, exp_alpha = self._explosions.build_segments(frame_idx=frame_idx)
        layers["explosions"] = FxLayerBatch(exp_segs, exp_alpha)

        imp_segs, imp_alpha = self._bursts.build_segments(frame_idx=frame_idx)
        layers["impacts"] = FxLayerBatch(imp_segs, imp_alpha)

        return FxFrameData(layers=layers)
