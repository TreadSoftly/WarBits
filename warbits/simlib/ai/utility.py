from __future__ import annotations

import dataclasses
import math
from typing import Callable, Dict, List, Optional, Sequence, Tuple

import numpy as np

from .context import AIContext
from .rng import DeterministicRNG


@dataclasses.dataclass(frozen=True)
class ScoreCurve:
    """Common scoring curves for utility systems."""

    kind: str
    a: float = 1.0
    b: float = 0.0

    def __call__(self, x: float) -> float:
        k = self.kind.lower()
        if k == "linear":
            return float(self.a * x + self.b)
        if k == "clamp01":
            return float(max(0.0, min(1.0, x)))
        if k == "logistic":
            # a controls steepness, b controls midpoint
            return float(1.0 / (1.0 + math.exp(-self.a * (x - self.b))))
        if k == "gaussian":
            # a = sigma, b = mean
            if self.a <= 0:
                return 0.0
            z = (x - self.b) / self.a
            return float(math.exp(-0.5 * z * z))
        if k == "inverse":
            # a/(x+b) with clamp
            denom = x + self.b
            if denom <= 1e-9:
                return 1.0
            return float(max(0.0, min(1.0, self.a / denom)))
        raise ValueError(f"Unknown ScoreCurve kind: {self.kind!r}")


@dataclasses.dataclass
class UtilityAction:
    """An action scored by a utility function."""

    name: str
    score_fn: Callable[[AIContext], float]
    act_fn: Callable[[AIContext], None]
    # Optional: minimum score required to be considered.
    min_score: float = -1e18


@dataclasses.dataclass
class UtilityPolicy:
    """Utility decision policy with deterministic tie-breaking and hysteresis.

    Features:
    - argmax selection by default
    - optional softmax sampling (temperature) for exploration
    - deterministic tie-breaking (stable + RNG-based when needed)
    - hysteresis: prevents thrashing when scores are close
    """

    actions: Sequence[UtilityAction]
    select_mode: str = "argmax"  # "argmax" or "softmax"
    temperature: float = 1.0  # used for softmax
    hysteresis_margin: float = 0.05
    last_action_key: str = "utility.last_action"

    def choose(self, ctx: AIContext) -> Optional[UtilityAction]:
        if not self.actions:
            return None

        scored: List[Tuple[float, int, UtilityAction]] = []
        for i, a in enumerate(self.actions):
            try:
                s = float(a.score_fn(ctx))
            except Exception:
                s = -1e18
            if s < a.min_score:
                continue
            scored.append((s, i, a))

        if not scored:
            return None

        # Stable sort by score then original order (for determinism)
        scored.sort(key=lambda t: (t[0], -t[1]))  # score asc
        best_score = scored[-1][0]

        # Hysteresis: keep last action if it's "close enough"
        last_name = ctx.bb.get(self.last_action_key, None)
        if last_name is not None:
            for s, _, a in scored:
                if a.name == last_name:
                    if s >= (best_score - self.hysteresis_margin):
                        return a
                    break

        if self.select_mode == "argmax":
            # Deterministic tie-break: if multiple within tiny epsilon, choose via RNG.
            eps = 1e-9
            top = [a for (s, _, a) in scored if s >= best_score - eps]
            if len(top) == 1:
                return top[0]
            # use RNG forked by time so it's stable per tick
            r = ctx.rng.fork("UtilityPolicy", ctx.now_s, len(top))
            return r.choice(top)

        if self.select_mode == "softmax":
            # Softmax over shifted scores for numerical stability
            t = float(self.temperature)
            if t <= 1e-9:
                # effectively argmax
                return scored[-1][2]
            scores = np.array([s for (s, _, _) in scored], dtype=np.float64)
            scores = scores - np.max(scores)
            probs = np.exp(scores / t)
            probs_sum = float(np.sum(probs))
            if not np.isfinite(probs_sum) or probs_sum <= 0.0:
                return scored[-1][2]
            probs = probs / probs_sum
            r = ctx.rng.fork("UtilityPolicySoftmax", ctx.now_s, len(scored))
            idx = r.weighted_index(probs.tolist())
            return scored[idx][2]

        raise ValueError(f"Unknown select_mode: {self.select_mode!r}")

    def tick(self, ctx: AIContext) -> Optional[str]:
        a = self.choose(ctx)
        if a is None:
            return None
        a.act_fn(ctx)
        ctx.bb.set(self.last_action_key, a.name)
        return a.name
