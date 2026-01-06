from __future__ import annotations

from enum import IntEnum


class LODLevel(IntEnum):
    """Discrete LOD tiers.

    The numeric ordering is meaningful:

    HIGH < MED < LOW < ICON

    That makes it easy to compare tiers.
    """

    HIGH = 0
    MED = 1
    LOW = 2
    ICON = 3
