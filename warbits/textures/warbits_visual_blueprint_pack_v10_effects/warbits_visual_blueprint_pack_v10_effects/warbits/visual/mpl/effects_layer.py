from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Tuple

import numpy as np

from warbits.visual.effects.types import FxFrameData, FxLayerBatch


@dataclass(frozen=True)
class MplFxColors:
    """Default per-layer colors for Matplotlib FX.

    Values are RGBA in 0..1.

    If you already have a `WireframeStyle`, you can pass your palette colors here.
    """

    tracers: Tuple[float, float, float, float] = (0.2, 1.0, 0.2, 1.0)
    contrails: Tuple[float, float, float, float] = (0.2, 0.8, 0.2, 0.55)
    explosions: Tuple[float, float, float, float] = (1.0, 0.55, 0.15, 0.95)
    impacts: Tuple[float, float, float, float] = (1.0, 0.35, 0.05, 0.95)


class MplFxLayer:
    """Draw FX batches into a Matplotlib 3D axes using pooled collections.

    Performance strategy
    --------------------
    - Create a small fixed number of `Line3DCollection` objects.
    - Update them in-place each frame using `.set_segments()` and `.set_color()`.
    - Reuse internal color buffers to reduce per-frame allocations.

    This is compatible with the rest of the WarBits visual blueprint system.
    """

    def __init__(
        self,
        ax,
        *,
        colors: MplFxColors | None = None,
        enable_glow: bool = True,
        glow_scale: float = 2.5,
        max_segments: Optional[Dict[str, int]] = None,
    ) -> None:
        try:
            from mpl_toolkits.mplot3d.art3d import Line3DCollection  # noqa: WPS433
        except Exception as exc:  # pragma: no cover
            raise RuntimeError(
                "Matplotlib 3D is required for MplFxLayer. "
                "Install matplotlib and ensure a 3D backend is available."
            ) from exc

        self._Line3DCollection = Line3DCollection
        self._ax = ax
        self._colors = colors or MplFxColors()
        self._enable_glow = bool(enable_glow)
        self._glow_scale = float(glow_scale)

        self._max_segments = dict(max_segments or {})

        # Layer -> (collection, glow_collection_or_none)
        self._layers: Dict[str, Tuple[object, Optional[object]]] = {}
        self._color_buf: Dict[str, np.ndarray] = {}

        for layer in ("tracers", "contrails", "explosions", "impacts"):
            self._init_layer(layer)

    def artists(self) -> list:
        """Return all Matplotlib artists owned by this layer."""

        arts = []
        for core, glow in self._layers.values():
            arts.append(core)
            if glow is not None:
                arts.append(glow)
        return arts

    def _init_layer(self, layer: str) -> None:
        base_rgba = np.array(getattr(self._colors, layer), dtype=np.float32)
        max_n = int(self._max_segments.get(layer, 0))
        if max_n <= 0:
            # Default: allow modest sizes without forcing user config.
            max_n = 4096 if layer in ("tracers", "contrails") else 2048

        # Prealloc color buffer.
        self._color_buf[layer] = np.zeros((max_n, 4), dtype=np.float32)

        core = self._Line3DCollection([], linewidths=1.0)
        core.set_color(base_rgba)
        self._ax.add_collection3d(core)

        glow = None
        if self._enable_glow:
            glow = self._Line3DCollection([], linewidths=1.0 * self._glow_scale)
            glow_rgba = base_rgba.copy()
            glow_rgba[3] = min(1.0, glow_rgba[3] * 0.25)
            glow.set_color(glow_rgba)
            self._ax.add_collection3d(glow)

        self._layers[layer] = (core, glow)

    def update(self, frame: FxFrameData) -> None:
        """Update artists to reflect FX for this frame."""

        for layer_name, (core, glow) in self._layers.items():
            batch = frame.layers.get(layer_name)
            if batch is None or batch.segments.size == 0:
                core.set_segments([])
                if glow is not None:
                    glow.set_segments([])
                continue

            segments = batch.segments
            alpha = batch.alpha

            # Clamp to buffer capacity.
            buf = self._color_buf[layer_name]
            n = int(min(len(alpha), len(buf)))
            if n <= 0:
                core.set_segments([])
                if glow is not None:
                    glow.set_segments([])
                continue

            base_rgba = np.array(getattr(self._colors, layer_name), dtype=np.float32)

            buf_view = buf[:n]
            # Fill RGB constant, alpha scaled per segment.
            buf_view[:, 0] = base_rgba[0]
            buf_view[:, 1] = base_rgba[1]
            buf_view[:, 2] = base_rgba[2]
            # Multiply base alpha by per-segment alpha (already 0..1).
            buf_view[:, 3] = base_rgba[3] * alpha[:n]

            core.set_segments(segments[:n])
            core.set_color(buf_view)

            if glow is not None:
                glow.set_segments(segments[:n])

