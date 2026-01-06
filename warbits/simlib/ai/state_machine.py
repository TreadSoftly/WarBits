from __future__ import annotations

import dataclasses
from typing import Callable, Dict, List, Optional, Sequence, Tuple

from .context import AIContext


@dataclasses.dataclass
class State:
    name: str
    on_enter: Optional[Callable[[AIContext], None]] = None
    on_exit: Optional[Callable[[AIContext], None]] = None
    on_tick: Optional[Callable[[AIContext], None]] = None


@dataclasses.dataclass(frozen=True)
class Transition:
    src: str
    dst: str
    cond: Callable[[AIContext], bool]
    priority: int = 0  # higher wins
    name: str = "transition"


@dataclasses.dataclass
class StateMachine:
    """A deterministic finite state machine.

    Determinism notes:
    - transitions are evaluated in a stable order: by priority desc then insertion order
    - only one transition can fire per tick (first match)
    """

    states: Dict[str, State]
    transitions: Sequence[Transition]
    initial: str
    current: str = dataclasses.field(init=False)

    def __post_init__(self) -> None:
        if self.initial not in self.states:
            raise KeyError(f"Initial state {self.initial!r} not in states")
        self.current = self.initial
        # stable sort once
        self._sorted_transitions = sorted(
            list(self.transitions),
            key=lambda t: (-t.priority, t.name, t.src, t.dst),
        )

    def reset(self, ctx: AIContext) -> None:
        self.current = self.initial
        st = self.states[self.current]
        if st.on_enter:
            st.on_enter(ctx)

    def tick(self, ctx: AIContext) -> str:
        # Evaluate transitions
        for t in self._sorted_transitions:
            if t.src != self.current:
                continue
            ok = False
            try:
                ok = bool(t.cond(ctx))
            except Exception:
                ok = False
            if not ok:
                continue
            # fire
            src_state = self.states[self.current]
            if src_state.on_exit:
                src_state.on_exit(ctx)
            self.current = t.dst
            dst_state = self.states[self.current]
            if dst_state.on_enter:
                dst_state.on_enter(ctx)
            break

        # tick current
        cur = self.states[self.current]
        if cur.on_tick:
            cur.on_tick(ctx)
        return self.current
