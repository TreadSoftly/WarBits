from __future__ import annotations

import time
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Iterator, List

from .stages import VisualStage


def _now_ns() -> int:
    # perf_counter_ns is monotonic and high resolution.
    return time.perf_counter_ns()


@dataclass(frozen=True)
class VisualFrameTimings:
    """Immutable per-frame timings.

    Durations are stored in nanoseconds for precision and to avoid floating noise.
    """

    frame_idx: int
    ns_by_stage: List[int]

    @property
    def ns_total(self) -> int:
        return int(sum(self.ns_by_stage))

    def ms_by_stage(self) -> List[float]:
        return [ns / 1e6 for ns in self.ns_by_stage]

    @property
    def ms_total(self) -> float:
        return self.ns_total / 1e6


class VisualPerf:
    """Low-allocation stage timing for renderers.

    Pattern:

        perf = VisualPerf()
        perf.begin_frame(i)
        perf.start(VisualStage.TERRAIN)
        ...
        perf.stop(VisualStage.TERRAIN)
        ...
        timings = perf.end_frame()

    Notes:

    - This is not a profiler. It’s a *frame-time budget tool*.
    - Stages are fixed by `VisualStage`.
    """

    def __init__(self) -> None:
        n = len(VisualStage)
        self._start_ns: List[int] = [0] * n
        self._accum_ns: List[int] = [0] * n
        self._frame_idx: int = -1

    def begin_frame(self, frame_idx: int) -> None:
        self._frame_idx = int(frame_idx)
        # Reset accumulators in-place to avoid allocating a new list.
        for i in range(len(self._accum_ns)):
            self._accum_ns[i] = 0
            self._start_ns[i] = 0

    def start(self, stage: VisualStage) -> None:
        self._start_ns[int(stage)] = _now_ns()

    def stop(self, stage: VisualStage) -> None:
        idx = int(stage)
        start = self._start_ns[idx]
        if start == 0:
            # stop() called without start(). We silently ignore in release.
            return
        self._accum_ns[idx] += _now_ns() - start
        self._start_ns[idx] = 0

    @contextmanager
    def scope(self, stage: VisualStage) -> Iterator[None]:
        """Convenience context manager.

        This allocates a small generator (contextmanager) so don’t use it inside
        the hottest inner loops if you’re allergic to allocations.
        """

        self.start(stage)
        try:
            yield
        finally:
            self.stop(stage)

    def end_frame(self) -> VisualFrameTimings:
        # Copy into a new list to freeze the sample.
        ns = list(self._accum_ns)
        return VisualFrameTimings(frame_idx=self._frame_idx, ns_by_stage=ns)

    @staticmethod
    def as_ms_dict(t: VisualFrameTimings) -> dict[str, float]:
        """Convert timings to a stable dict (useful for JSONL logs)."""

        return {
            "frame": float(t.frame_idx),
            "terrain_ms": t.ns_by_stage[int(VisualStage.TERRAIN)] / 1e6,
            "entities_ms": t.ns_by_stage[int(VisualStage.ENTITIES)] / 1e6,
            "projectiles_ms": t.ns_by_stage[int(VisualStage.PROJECTILES)] / 1e6,
            "hud_ms": t.ns_by_stage[int(VisualStage.HUD)] / 1e6,
            "effects_ms": t.ns_by_stage[int(VisualStage.EFFECTS)] / 1e6,
            "total_ms": t.ms_total,
        }
