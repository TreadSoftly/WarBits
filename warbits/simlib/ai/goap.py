from __future__ import annotations

import dataclasses
import heapq
from typing import Dict, FrozenSet, List, Optional, Sequence, Tuple

from .rng import DeterministicRNG


GoapState = FrozenSet[Tuple[str, bool]]


def state_get(state: GoapState, key: str, default: bool = False) -> bool:
    for k, v in state:
        if k == key:
            return bool(v)
    return bool(default)


def state_set(state: GoapState, key: str, value: bool) -> GoapState:
    d = dict(state)
    d[key] = bool(value)
    return frozenset(d.items())


def state_satisfies(state: GoapState, goal: Dict[str, bool]) -> bool:
    for k, v in goal.items():
        if state_get(state, k) != bool(v):
            return False
    return True


@dataclasses.dataclass(frozen=True)
class GoapAction:
    """A GOAP action with boolean preconditions/effects.

    This is intentionally small and deterministic. It is a great fit for:
    - mission-level AI (patrol -> engage -> evade)
    - ground unit logic
    - high-level aircraft behavior mode switching

    Not a fit for:
    - continuous control (that's what utility/BT is for)
    """

    name: str
    cost: float
    pre: Dict[str, bool]
    eff: Dict[str, bool]

    def applicable(self, state: GoapState) -> bool:
        for k, v in self.pre.items():
            if state_get(state, k) != bool(v):
                return False
        return True

    def apply(self, state: GoapState) -> GoapState:
        s = state
        for k, v in self.eff.items():
            s = state_set(s, k, bool(v))
        return s


@dataclasses.dataclass
class GoapPlanner:
    """Deterministic A* planner for small boolean GOAP problems."""

    actions: Sequence[GoapAction]
    rng: DeterministicRNG
    max_expansions: int = 5000

    def plan(self, start: GoapState, goal: Dict[str, bool]) -> Optional[List[GoapAction]]:
        if state_satisfies(start, goal):
            return []

        # A* with heuristic = number of unsatisfied goal vars
        def h(s: GoapState) -> float:
            miss = 0
            for k, v in goal.items():
                if state_get(s, k) != bool(v):
                    miss += 1
            return float(miss)

        # deterministic action order: sort by name then cost
        acts = list(self.actions)
        # Keep caller-provided order (deterministic and user-prioritizable).

        open_heap: List[Tuple[float, float, int, GoapState]] = []
        g_score: Dict[GoapState, float] = {start: 0.0}
        came_from: Dict[GoapState, Tuple[GoapState, GoapAction]] = {}

        # tie-break counter to keep heap deterministic
        counter = 0
        heapq.heappush(open_heap, (h(start), 0.0, counter, start))

        expansions = 0
        while open_heap and expansions < self.max_expansions:
            _, g, _, current = heapq.heappop(open_heap)
            expansions += 1

            if state_satisfies(current, goal):
                # reconstruct
                path: List[GoapAction] = []
                s = current
                while s in came_from:
                    prev, act = came_from[s]
                    path.append(act)
                    s = prev
                path.reverse()
                return path

            # expand
            for act in acts:
                if not act.applicable(current):
                    continue
                nxt = act.apply(current)
                ng = float(g) + float(act.cost)
                if nxt not in g_score or ng < g_score[nxt] - 1e-12:
                    g_score[nxt] = ng
                    came_from[nxt] = (current, act)
                    counter += 1
                    f = ng + h(nxt)
                    heapq.heappush(open_heap, (f, ng, counter, nxt))

        return None
