"""Performance helpers for WarBits visuals.

This package is intentionally small and renderer-agnostic:

- `VisualPerf`: low-allocation stage timers per frame
- `VisualBudget`: simple budget checks (tripwires)

The goal is *smooth frame time*, not religious micro-optimizing.
"""

from .stages import VisualStage
from .stats import VisualPerf, VisualFrameTimings, ns_to_ms
from .budget import VisualBudget, BudgetViolation

__all__ = [
    "VisualStage",
    "VisualPerf",
    "VisualFrameTimings",
    "VisualBudget",
    "BudgetViolation",
    "ns_to_ms",
]
