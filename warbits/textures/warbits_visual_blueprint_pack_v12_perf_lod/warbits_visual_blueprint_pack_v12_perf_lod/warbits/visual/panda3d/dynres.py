from __future__ import annotations

from dataclasses import dataclass


@dataclass
class DynamicResolutionScaler:
    """A tiny dynamic resolution controller.

    This is meant for Panda3D (or any GPU renderer) when you want to prioritize
    **smooth frame time**.

    It does not do any render-to-texture itself.
    It only computes a `render_scale` multiplier (0.25..1.0 by default) that your renderer can use when sizing offscreen buffers.

    The idea:
    - If last frame was slower than target ms, scale down a bit.
    - If frames are comfortably faster, scale back up slowly.

    This is *much* less jarring than suddenly dropping LOD everywhere.
    """

    target_ms: float = 8.0
    min_scale: float = 0.5
    max_scale: float = 1.0
    down_rate: float = 0.92  # multiply scale when too slow
    up_rate: float = 1.01  # multiply scale when fast

    render_scale: float = 1.0

    def update(self, last_frame_ms: float) -> float:
        if last_frame_ms <= 0:
            return self.render_scale

        if last_frame_ms > self.target_ms:
            self.render_scale *= self.down_rate
        else:
            self.render_scale *= self.up_rate

        if self.render_scale < self.min_scale:
            self.render_scale = self.min_scale
        elif self.render_scale > self.max_scale:
            self.render_scale = self.max_scale

        return self.render_scale
