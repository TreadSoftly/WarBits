"""Performance measurement helpers.

These are tiny tools intended for:
- frame timing breakdowns (sim vs render vs physics kernels)
- regression detection (compare baseline vs current)
- avoiding "perf rot" as realism grows

This is NOT a full profiler replacement.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterator, Optional
import time
from contextlib import contextmanager


@dataclass
class RunningStat:
    """Welford running mean/variance."""

    n: int = 0
    mean: float = 0.0
    m2: float = 0.0
    min_v: float = float("inf")
    max_v: float = float("-inf")

    def push(self, x: float) -> None:
        x = float(x)
        self.n += 1
        delta = x - self.mean
        self.mean += delta / self.n
        delta2 = x - self.mean
        self.m2 += delta * delta2
        self.min_v = x if x < self.min_v else self.min_v
        self.max_v = x if x > self.max_v else self.max_v

    @property
    def variance(self) -> float:
        if self.n < 2:
            return 0.0
        return self.m2 / (self.n - 1)

    @property
    def std(self) -> float:
        return self.variance ** 0.5


@dataclass
class FrameProfiler:
    """Collect per-section timing stats."""

    stats_ms: Dict[str, RunningStat] = field(default_factory=dict)
    _t0: float = field(default=0.0, init=False)
    _active_section: Optional[str] = field(default=None, init=False)

    def begin_frame(self) -> None:
        self._t0 = time.perf_counter()
        self._active_section = None

    def end_frame(self) -> None:
        # no-op placeholder (could record total)
        return

    @contextmanager
    def section(self, name: str) -> Iterator[None]:
        t_start = time.perf_counter()
        self._active_section = name
        try:
            yield
        finally:
            dt_ms = (time.perf_counter() - t_start) * 1000.0
            self.stats_ms.setdefault(name, RunningStat()).push(dt_ms)
            self._active_section = None

    def summary(self) -> Dict[str, Dict[str, float]]:
        out: Dict[str, Dict[str, float]] = {}
        for k, s in self.stats_ms.items():
            out[k] = {
                "n": float(s.n),
                "mean_ms": float(s.mean),
                "std_ms": float(s.std),
                "min_ms": float(s.min_v if s.min_v != float("inf") else 0.0),
                "max_ms": float(s.max_v if s.max_v != float("-inf") else 0.0),
            }
        return out
