from __future__ import annotations

from enum import IntEnum


class VisualStage(IntEnum):
    """Fixed set of renderer stages we time.

    Keep this list *stable*. It is used by tests and by tooling.

    We intentionally avoid a `dict[str, ...]` timing map in the hot path.
    Using an enum lets us store times in a fixed-size list.
    """

    TERRAIN = 0
    ENTITIES = 1
    PROJECTILES = 2
    HUD = 3
    EFFECTS = 4

    # NOTE: TOTAL is derived (sum of above). We don’t time it directly.
