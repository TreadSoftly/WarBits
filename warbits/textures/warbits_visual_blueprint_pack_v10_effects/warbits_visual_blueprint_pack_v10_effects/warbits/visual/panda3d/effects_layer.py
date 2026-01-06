from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Tuple

import numpy as np

from warbits.visual.effects.types import FxFrameData


@dataclass(frozen=True)
class P3DFxColors:
    """Default per-layer colors for Panda3D FX (RGBA 0..1)."""

    tracers: Tuple[float, float, float, float] = (0.2, 1.0, 0.2, 1.0)
    contrails: Tuple[float, float, float, float] = (0.2, 0.8, 0.2, 0.55)
    explosions: Tuple[float, float, float, float] = (1.0, 0.55, 0.15, 0.95)
    impacts: Tuple[float, float, float, float] = (1.0, 0.35, 0.05, 0.95)


class P3DFxLayer:
    """Render FX batches with Panda3D using LineBatch pooling."""

    def __init__(
        self,
        parent_np,
        *,
        colors: P3DFxColors | None = None,
        enable_glow: bool = True,
        glow_scale: float = 2.5,
        max_segments: Optional[Dict[str, int]] = None,
        thickness: float = 1.0,
    ) -> None:
        try:
            from warbits.visual.panda3d.line_batch import LineBatch  # noqa: WPS433
        except Exception as exc:  # pragma: no cover
            raise RuntimeError(
                "Panda3D is required for P3DFxLayer. Install panda3d and the WarBits Panda3D visual pack."
            ) from exc

        self._parent = parent_np
        self._LineBatch = LineBatch
        self._colors = colors or P3DFxColors()
        self._enable_glow = bool(enable_glow)
        self._glow_scale = float(glow_scale)
        self._max_segments = dict(max_segments or {})
        self._thickness = float(thickness)

        # Layer -> (core_batch, glow_batch_or_none)
        self._layers: Dict[str, Tuple[LineBatch, Optional[LineBatch]]] = {}
        self._color_buf: Dict[str, np.ndarray] = {}

        for layer in ("tracers", "contrails", "explosions", "impacts"):
            self._init_layer(layer)

    def _init_layer(self, layer: str) -> None:
        max_n = int(self._max_segments.get(layer, 0))
        if max_n <= 0:
            max_n = 4096 if layer in ("tracers", "contrails") else 2048

        # Panda3D colors are per-vertex; we store (2N,4) because each segment has two vertices.
        self._color_buf[layer] = np.zeros((max_n * 2, 4), dtype=np.float32)

        core = self._LineBatch(name=f"fx_{layer}")
        core_np = core.attach_to(self._parent)
        # Thickness is not guaranteed on all backends, but safe to request.
        try:
            core_np.setRenderModeThickness(self._thickness)
        except Exception:
            pass

        glow = None
        if self._enable_glow:
            glow = self._LineBatch(name=f"fx_{layer}_glow")
            glow_np = glow.attach_to(self._parent)
            try:
                glow_np.setRenderModeThickness(self._thickness * self._glow_scale)
            except Exception:
                pass

        self._layers[layer] = (core, glow)

    def update(self, frame: FxFrameData) -> None:
        for layer_name, (core, glow) in self._layers.items():
            batch = frame.layers.get(layer_name)
            if batch is None or batch.segments.size == 0:
                core.set_segments(np.zeros((0, 2, 3), dtype=np.float32))
                if glow is not None:
                    glow.set_segments(np.zeros((0, 2, 3), dtype=np.float32))
                continue

            segments = batch.segments
            alpha = batch.alpha

            max_n = len(self._color_buf[layer_name]) // 2
            n = int(min(len(alpha), max_n))
            if n <= 0:
                core.set_segments(np.zeros((0, 2, 3), dtype=np.float32))
                if glow is not None:
                    glow.set_segments(np.zeros((0, 2, 3), dtype=np.float32))
                continue

            base = np.array(getattr(self._colors, layer_name), dtype=np.float32)
            buf = self._color_buf[layer_name]
            buf_view = buf[: n * 2]

            # Repeat per-segment alpha for both vertices.
            a2 = np.repeat(alpha[:n], 2)
            buf_view[:, 0] = base[0]
            buf_view[:, 1] = base[1]
            buf_view[:, 2] = base[2]
            buf_view[:, 3] = base[3] * a2

            core.set_segments(segments[:n], colors=buf_view)
            if glow is not None:
                glow.set_segments(segments[:n])

