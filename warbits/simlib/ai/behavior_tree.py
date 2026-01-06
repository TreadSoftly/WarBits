from __future__ import annotations

import dataclasses
import enum
from typing import Callable, List, Optional, Sequence

from .context import AIContext


class Status(enum.Enum):
    SUCCESS = 1
    FAILURE = 2
    RUNNING = 3


class Node:
    """Behavior Tree node base class."""

    def tick(self, ctx: AIContext) -> Status:
        raise NotImplementedError

    def reset(self) -> None:
        # default: stateless
        return

    def __repr__(self) -> str:
        return self.__class__.__name__


@dataclasses.dataclass
class Condition(Node):
    fn: Callable[[AIContext], bool]
    name: str = "cond"

    def tick(self, ctx: AIContext) -> Status:
        try:
            ok = bool(self.fn(ctx))
        except Exception:
            # Conditions should be side-effect-free. Fail closed.
            ok = False
        return Status.SUCCESS if ok else Status.FAILURE

    def __repr__(self) -> str:
        return f"Condition({self.name})"


@dataclasses.dataclass
class Action(Node):
    fn: Callable[[AIContext], Status]
    name: str = "action"

    def tick(self, ctx: AIContext) -> Status:
        return self.fn(ctx)

    def __repr__(self) -> str:
        return f"Action({self.name})"


@dataclasses.dataclass
class Sequence(Node):
    children: Sequence[Node]
    memory: bool = True
    _idx: int = 0

    def tick(self, ctx: AIContext) -> Status:
        start = self._idx if self.memory else 0
        i = start
        while i < len(self.children):
            st = self.children[i].tick(ctx)
            if st is Status.SUCCESS:
                i += 1
                continue
            if st is Status.FAILURE:
                if self.memory:
                    self._idx = 0
                return Status.FAILURE
            # RUNNING
            if self.memory:
                self._idx = i
            return Status.RUNNING
        if self.memory:
            self._idx = 0
        return Status.SUCCESS

    def reset(self) -> None:
        self._idx = 0
        for c in self.children:
            c.reset()

    def __repr__(self) -> str:
        return f"Sequence({len(self.children)})"


@dataclasses.dataclass
class Selector(Node):
    children: Sequence[Node]
    memory: bool = True
    _idx: int = 0

    def tick(self, ctx: AIContext) -> Status:
        start = self._idx if self.memory else 0
        i = start
        while i < len(self.children):
            st = self.children[i].tick(ctx)
            if st is Status.FAILURE:
                i += 1
                continue
            if st is Status.SUCCESS:
                if self.memory:
                    self._idx = 0
                return Status.SUCCESS
            # RUNNING
            if self.memory:
                self._idx = i
            return Status.RUNNING
        if self.memory:
            self._idx = 0
        return Status.FAILURE

    def reset(self) -> None:
        self._idx = 0
        for c in self.children:
            c.reset()

    def __repr__(self) -> str:
        return f"Selector({len(self.children)})"


@dataclasses.dataclass
class RandomSelector(Node):
    """Selector that evaluates children in a deterministic shuffled order each tick."""

    children: Sequence[Node]
    memory: bool = False

    def tick(self, ctx: AIContext) -> Status:
        idxs = list(range(len(self.children)))
        # Deterministic per-tick shuffle: key by time bucket to avoid jitter.
        # You can override by forking ctx.rng before ticking this node.
        r = ctx.rng.fork("RandomSelector", ctx.now_s, len(self.children))
        r.shuffle_in_place(idxs)
        for i in idxs:
            st = self.children[i].tick(ctx)
            if st is Status.FAILURE:
                continue
            return st
        return Status.FAILURE

    def reset(self) -> None:
        for c in self.children:
            c.reset()

    def __repr__(self) -> str:
        return f"RandomSelector({len(self.children)})"


@dataclasses.dataclass
class Parallel(Node):
    """Tick all children.

    Parameters:
    - success_threshold: how many children must succeed to succeed.
    - failure_threshold: how many must fail to fail.
      If both thresholds are None, defaults to:
        success_threshold=len(children), failure_threshold=1 (classic 'AND' parallel)

    Memory:
    - children are not reset automatically; caller can reset tree on mode changes.
    """

    children: Sequence[Node]
    success_threshold: Optional[int] = None
    failure_threshold: Optional[int] = None

    def tick(self, ctx: AIContext) -> Status:
        if not self.children:
            return Status.SUCCESS
        succ_t = self.success_threshold if self.success_threshold is not None else len(self.children)
        fail_t = self.failure_threshold if self.failure_threshold is not None else 1

        succ = 0
        fail = 0
        running = 0
        for c in self.children:
            st = c.tick(ctx)
            if st is Status.SUCCESS:
                succ += 1
            elif st is Status.FAILURE:
                fail += 1
            else:
                running += 1

        if succ >= succ_t:
            return Status.SUCCESS
        if fail >= fail_t:
            return Status.FAILURE
        return Status.RUNNING

    def reset(self) -> None:
        for c in self.children:
            c.reset()

    def __repr__(self) -> str:
        return f"Parallel({len(self.children)})"


# ---- decorators ----

@dataclasses.dataclass
class Inverter(Node):
    child: Node

    def tick(self, ctx: AIContext) -> Status:
        st = self.child.tick(ctx)
        if st is Status.SUCCESS:
            return Status.FAILURE
        if st is Status.FAILURE:
            return Status.SUCCESS
        return Status.RUNNING

    def reset(self) -> None:
        self.child.reset()


@dataclasses.dataclass
class Succeeder(Node):
    child: Node

    def tick(self, ctx: AIContext) -> Status:
        _ = self.child.tick(ctx)
        return Status.SUCCESS

    def reset(self) -> None:
        self.child.reset()


@dataclasses.dataclass
class Failer(Node):
    child: Node

    def tick(self, ctx: AIContext) -> Status:
        _ = self.child.tick(ctx)
        return Status.FAILURE

    def reset(self) -> None:
        self.child.reset()


@dataclasses.dataclass
class Repeat(Node):
    child: Node
    count: Optional[int] = None  # None => infinite
    until: Optional[Status] = None  # e.g., repeat until SUCCESS
    _done: int = 0

    def tick(self, ctx: AIContext) -> Status:
        if self.count is not None and self._done >= self.count:
            return Status.SUCCESS
        st = self.child.tick(ctx)
        if self.until is not None and st is self.until:
            self._done = 0
            return st
        if st is Status.RUNNING:
            return Status.RUNNING
        # completed one iteration
        self._done += 1
        self.child.reset()
        if self.count is not None and self._done >= self.count:
            self._done = 0
            return Status.SUCCESS
        return Status.RUNNING

    def reset(self) -> None:
        self._done = 0
        self.child.reset()


@dataclasses.dataclass
class Cooldown(Node):
    """Gate a child so it cannot succeed more often than every cooldown_s seconds.

    This is useful to prevent spamming actions like 'fire rocket' every frame.

    Storage:
    - uses blackboard key: cooldown.<id>.last_success
    """

    child: Node
    cooldown_s: float
    id: str = "default"

    def tick(self, ctx: AIContext) -> Status:
        key = f"cooldown.{self.id}.last_success"
        last = float(ctx.bb.get(key, -1e18))
        if (ctx.now_s - last) < self.cooldown_s:
            return Status.FAILURE
        st = self.child.tick(ctx)
        if st is Status.SUCCESS:
            ctx.bb.set(key, float(ctx.now_s))
        return st

    def reset(self) -> None:
        self.child.reset()


@dataclasses.dataclass
class Timeout(Node):
    """Fail the child if it runs longer than timeout_s.

    Storage:
    - uses blackboard key: timeout.<id>.start_time
    """

    child: Node
    timeout_s: float
    id: str = "default"

    def tick(self, ctx: AIContext) -> Status:
        key = f"timeout.{self.id}.start_time"
        start = ctx.bb.get(key, None)
        if start is None:
            ctx.bb.set(key, float(ctx.now_s))
            start = float(ctx.now_s)
        if (ctx.now_s - float(start)) > self.timeout_s:
            # reset timer on failure so subsequent ticks can try again.
            ctx.bb.delete(key)
            self.child.reset()
            return Status.FAILURE
        st = self.child.tick(ctx)
        if st is not Status.RUNNING:
            ctx.bb.delete(key)
        return st

    def reset(self) -> None:
        ctx_key = f"timeout.{self.id}.start_time"
        # can't access ctx here; rely on caller to clear blackboard if needed
        self.child.reset()


@dataclasses.dataclass
class BehaviorTree:
    root: Node

    def tick(self, ctx: AIContext) -> Status:
        return self.root.tick(ctx)

    def reset(self) -> None:
        self.root.reset()
