"""Deterministic spatial hashing for broadphase queries.

This is a pragmatic performance tool:
- Put entities into grid buckets (cell_size meters).
- Query nearby cells for candidate pairs before doing exact geometry.

Notes on determinism:
- Dict iteration order is insertion-ordered in modern Python, but we still sort
  cell keys during queries to keep results stable even if insertion order differs.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Iterable

Cell = tuple[int, int, int]


def _empty_cells() -> dict[Cell, list[int]]:
    return {}


def _cell_index(x: float, cell_size: float) -> int:
    return int(math.floor(x / cell_size))


@dataclass
class SpatialHash3D:
    cell_size: float
    _cells: dict[Cell, list[int]] = field(default_factory=_empty_cells)

    def clear(self) -> None:
        self._cells.clear()

    def insert(self, obj_id: int, x: float, y: float, z: float) -> None:
        if self.cell_size <= 0:
            raise ValueError("cell_size must be positive")
        c = (_cell_index(x, self.cell_size), _cell_index(y, self.cell_size), _cell_index(z, self.cell_size))
        self._cells.setdefault(c, []).append(int(obj_id))

    def insert_many(self, obj_ids: Iterable[int], positions_xyz: Iterable[tuple[float, float, float]]) -> None:
        for oid, (x, y, z) in zip(obj_ids, positions_xyz):
            self.insert(int(oid), float(x), float(y), float(z))

    def query_radius(self, x: float, y: float, z: float, radius: float) -> list[int]:
        """Return candidate ids within radius based on grid neighborhood (not exact distance)."""
        if radius < 0:
            return []
        cx = _cell_index(x, self.cell_size)
        cy = _cell_index(y, self.cell_size)
        cz = _cell_index(z, self.cell_size)
        r_cells = int(math.ceil(radius / self.cell_size))

        candidates: list[int] = []
        # Sort keys deterministically by iterating ranges in deterministic order.
        for ix in range(cx - r_cells, cx + r_cells + 1):
            for iy in range(cy - r_cells, cy + r_cells + 1):
                for iz in range(cz - r_cells, cz + r_cells + 1):
                    key = (ix, iy, iz)
                    if key in self._cells:
                        candidates.extend(self._cells[key])

        # Deduplicate while keeping a stable order (first occurrence wins)
        seen: set[int] = set()
        out: list[int] = []
        for cid in candidates:
            if cid not in seen:
                seen.add(cid)
                out.append(cid)
        return out
