from __future__ import annotations

import dataclasses
from typing import Any, Dict, Iterable, Iterator, Mapping, MutableMapping, Optional, Tuple


@dataclasses.dataclass
class Blackboard:
    """A simple shared memory store for AI systems.

    Features:
    - namespacing via dot keys: "combat.target_id"
    - optional write history for debugging
    - stable get/set semantics (no magic defaults)

    This deliberately stays small: it's a dict with a few guardrails.
    """

    data: Dict[str, Any] = dataclasses.field(default_factory=dict)
    enable_history: bool = False
    _history: list[Tuple[str, Any]] = dataclasses.field(default_factory=list, init=False, repr=False)

    def get(self, key: str, default: Any = None) -> Any:
        return self.data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self.data[key] = value
        if self.enable_history:
            self._history.append((key, value))

    def has(self, key: str) -> bool:
        return key in self.data

    def require(self, key: str) -> Any:
        if key not in self.data:
            raise KeyError(f"Blackboard missing required key: {key!r}")
        return self.data[key]

    def delete(self, key: str) -> None:
        if key in self.data:
            del self.data[key]
            if self.enable_history:
                self._history.append((key, None))

    def prefix(self, namespace: str) -> "BlackboardView":
        return BlackboardView(self, namespace)

    def snapshot(self) -> Dict[str, Any]:
        # shallow copy; values may be mutable by design
        return dict(self.data)

    def history(self) -> list[Tuple[str, Any]]:
        return list(self._history)


@dataclasses.dataclass(frozen=True)
class BlackboardView:
    """A namespaced view of a Blackboard.

    Example:
        bb = Blackboard()
        combat = bb.prefix("combat")
        combat.set("target_id", "bogie-1")  # stores at "combat.target_id"
    """
    bb: Blackboard
    namespace: str

    def _k(self, key: str) -> str:
        ns = self.namespace.rstrip(".")
        k = key.lstrip(".")
        return f"{ns}.{k}" if ns else k

    def get(self, key: str, default: Any = None) -> Any:
        return self.bb.get(self._k(key), default)

    def set(self, key: str, value: Any) -> None:
        self.bb.set(self._k(key), value)

    def has(self, key: str) -> bool:
        return self.bb.has(self._k(key))

    def require(self, key: str) -> Any:
        return self.bb.require(self._k(key))

    def delete(self, key: str) -> None:
        self.bb.delete(self._k(key))
