from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Any, Callable

import numpy as np

from ..simlib.rng import DeterministicRNG


TerrainHeightFn = Callable[..., Any]


def _new_py_rngs() -> dict[str, random.Random]:
    return {}


def _new_np_rngs() -> dict[str, np.random.Generator]:
    return {}


@dataclass
class TerrainQuery:
    height: TerrainHeightFn


@dataclass
class SimClock:
    dt_s: float
    frame: int = 0
    time_s: float = 0.0

    def tick(self, frame: int) -> None:
        self.frame = int(frame)
        self.time_s = float(self.frame) * float(self.dt_s)


@dataclass
class SimServices:
    rng: DeterministicRNG
    clock: SimClock
    terrain: TerrainQuery
    config: Any
    data: Any | None = None
    _py_rngs: dict[str, random.Random] = field(
        default_factory=_new_py_rngs, init=False, repr=False
    )
    _np_rngs: dict[str, np.random.Generator] = field(
        default_factory=_new_np_rngs, init=False, repr=False
    )

    def substream(self, label: str) -> DeterministicRNG:
        return self.rng.split(label)

    def py_random(self, label: str) -> random.Random:
        cached = self._py_rngs.get(label)
        if cached is not None:
            return cached
        sub = self.substream(label)
        rng = random.Random(int(sub.root_seed_u64))
        self._py_rngs[label] = rng
        return rng

    def numpy_rng(self, label: str) -> np.random.Generator:
        cached = self._np_rngs.get(label)
        if cached is not None:
            return cached
        sub = self.substream(label)
        rng = sub.generator()
        self._np_rngs[label] = rng
        return rng

    def reset_rngs(self) -> None:
        self._py_rngs.clear()
        self._np_rngs.clear()
