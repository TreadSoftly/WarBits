from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

import numpy as np


FxLayerName = str


@dataclass
class FxLayerBatch:
    """One line layer (segments + per-segment alpha)."""

    segments: np.ndarray  # (N,2,3) float32
    alpha: np.ndarray  # (N,) float32


@dataclass
class FxFrameData:
    """All FX geometry for a single frame."""

    layers: Dict[FxLayerName, FxLayerBatch]

    def get(self, name: FxLayerName) -> Optional[FxLayerBatch]:
        return self.layers.get(name)


def empty_layer() -> FxLayerBatch:
    return FxLayerBatch(
        segments=np.zeros((0, 2, 3), dtype=np.float32),
        alpha=np.zeros((0,), dtype=np.float32),
    )
