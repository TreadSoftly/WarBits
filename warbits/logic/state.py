from __future__ import annotations

# ─────────────────────────────────────────────────────────────────────────────
# logic/state.py – contiguous, NumPy-backed runtime state
# ─────────────────────────────────────────────────────────────────────────────
from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, TypeAlias

from ..config import settings as _cfg
from ..core.events import DebugEvent, ExplosionEvent, ImpactEvent, ParachuteEvent

import numpy as np
import numpy.typing as npt

Vector3: TypeAlias = tuple[float, float, float]
ExplosionState: TypeAlias = ExplosionEvent
ParachuteState: TypeAlias = ParachuteEvent


def _new_explosions() -> list[ExplosionEvent]:
    return []


def _new_parachutes() -> list[ParachuteEvent]:
    return []


def _new_impacts() -> list[ImpactEvent]:
    return []

def _new_debug_events() -> list[DebugEvent]:
    return []


if TYPE_CHECKING:                       # precise typing for static analysers
    _F32Arr = npt.NDArray[np.float32]
else:                                   # runtime – keep it fast
    _F32Arr = Any                        # type: ignore

_MAX_PROJECTILES = 8_192
_MAX_SAMPLES    = 2_048

# --------------------------------------------------------------------------- #
# contiguous SOA buffer
# --------------------------------------------------------------------------- #
class ProjectileBuffer:
    """Struct-of-arrays trajectory store backing every projectile family."""
    def __init__(
        self,
        *,
        capacity: int     = _MAX_PROJECTILES,
        max_samples: int  = _MAX_SAMPLES,
    ) -> None:
        self.capacity    = int(capacity)
        self.max_samples = int(max_samples)

        self._paths        : _F32Arr | None               = None
        self._lengths      : npt.NDArray[np.int32] | None = None
        self._sample_index : npt.NDArray[np.int32] | None = None
        self._active_pos   : npt.NDArray[np.int32] | None = None
        self._artists      : list[Any]                    = [None] * capacity
        self._cursor       : int                          = 0
        self._active_rows  : list[int]                    = []

    def _ensure_allocated(self) -> None:
        if self._paths is not None:
            return
        self._paths = np.zeros((self.capacity, 3, self.max_samples), dtype=np.float32)
        self._lengths = np.zeros(self.capacity, dtype=np.int32)
        self._sample_index = np.zeros(self.capacity, dtype=np.int32)
        self._active_pos = np.full(self.capacity, -1, dtype=np.int32)

    def _resize_samples(self, new_max: int) -> None:
        new_max = int(new_max)
        if new_max <= self.max_samples:
            return
        if self._paths is None:
            self.max_samples = new_max
            return
        new_paths = np.zeros((self.capacity, 3, new_max), dtype=np.float32)
        new_paths[:, :, : self.max_samples] = self._paths
        self._paths = new_paths
        self.max_samples = new_max

    def _activate_row(self, row: int) -> None:
        if self._active_pos is None:
            return
        pos = int(self._active_pos[row])
        if pos != -1:
            return
        self._active_pos[row] = len(self._active_rows)
        self._active_rows.append(row)

    def _deactivate_row(self, row: int) -> None:
        if self._active_pos is None:
            return
        pos = int(self._active_pos[row])
        if pos == -1:
            return
        last_row = self._active_rows[-1]
        self._active_rows[pos] = last_row
        self._active_pos[last_row] = pos
        self._active_rows.pop()
        self._active_pos[row] = -1

    # container helpers ------------------------------------------------------
    def __len__(self) -> int:
        return len(self._active_rows)

    def __iter__(self) -> Iterator[int]:
        if not self._active_rows:
            return iter(())
        return iter(self._active_rows)

    # quick views (read-only) -----------------------------------------------
    @property
    def paths(self) -> _F32Arr:
        if self._paths is None or self._lengths is None or not self._active_rows:
            return np.empty((0, 3, self.max_samples), dtype=np.float32)
        return self._paths[self._active_rows]

    @property
    def lengths(self) -> npt.NDArray[np.int32]:
        if self._lengths is None or not self._active_rows:
            return np.empty(0, dtype=np.int32)
        return self._lengths[self._active_rows]

    @property
    def sample_index(self) -> npt.NDArray[np.int32]:
        if self._sample_index is None or self._lengths is None or not self._active_rows:
            return np.empty(0, dtype=np.int32)
        return self._sample_index[self._active_rows]

    def sample_positions(
        self,
    ) -> tuple[_F32Arr, _F32Arr, _F32Arr, npt.NDArray[np.int32]]:
        if self._paths is None or self._lengths is None or self._sample_index is None:
            empty_f = np.empty(0, dtype=np.float32)
            empty_i = np.empty(0, dtype=np.int32)
            return empty_f, empty_f, empty_f, empty_i
        if not self._active_rows:
            empty_f = np.empty(0, dtype=np.float32)
            empty_i = np.empty(0, dtype=np.int32)
            return empty_f, empty_f, empty_f, empty_i
        rows = np.asarray(self._active_rows, dtype=np.int32)
        idx = self._sample_index[rows]
        xs = self._paths[rows, 0, idx]
        ys = self._paths[rows, 1, idx]
        zs = self._paths[rows, 2, idx]
        return xs, ys, zs, rows

    # ---------------------------------------------------------------------- #
    # mutating API
    # ---------------------------------------------------------------------- #
    def add(
        self,
        traj_x: _F32Arr | npt.NDArray[np.floating[Any]],
        traj_y: _F32Arr | npt.NDArray[np.floating[Any]],
        traj_z: _F32Arr | npt.NDArray[np.floating[Any]],
    ) -> Iterable[int]:
        self._ensure_allocated()
        traj_x = np.asarray(traj_x, dtype=np.float32)
        traj_y = np.asarray(traj_y, dtype=np.float32)
        traj_z = np.asarray(traj_z, dtype=np.float32)

        if traj_x.ndim == 1:        # promote single row → (1,T)
            traj_x = traj_x[None, :]
            traj_y = traj_y[None, :]
            traj_z = traj_z[None, :]

        if not (traj_x.shape == traj_y.shape == traj_z.shape):
            raise ValueError("x / y / z shapes must match exactly")

        n_new, n_samples = traj_x.shape
        if n_new > self.capacity:
            raise ValueError("trajectory batch exceeds buffer capacity")
        if n_samples > self.max_samples:
            if _cfg.PROJECTILE_AUTO_RESIZE:
                self._resize_samples(n_samples)
            elif _cfg.STRICT_PHYSICS:
                raise ValueError("trajectory exceeds buffer max_samples")
            else:
                n_samples = self.max_samples
                traj_x = traj_x[:, :n_samples]
                traj_y = traj_y[:, :n_samples]
                traj_z = traj_z[:, :n_samples]

        assert self._paths is not None
        assert self._lengths is not None
        assert self._sample_index is not None
        rows = (np.arange(n_new, dtype=np.int32) + self._cursor) % self.capacity
        rows_list = rows.tolist()
        if self._lengths[rows].any():
            # Overwrite oldest slots in ring-buffer order.
            self.remove(rows_list)

        self._paths[rows, 0, :n_samples] = traj_x
        self._paths[rows, 1, :n_samples] = traj_y
        self._paths[rows, 2, :n_samples] = traj_z

        self._lengths[rows]      = n_samples
        self._sample_index[rows] = 0
        for r in rows_list:
            self._artists[r] = None
            self._activate_row(r)

        self._cursor = int((self._cursor + n_new) % self.capacity)
        return rows_list

    def step(self) -> None:
        if self._lengths is None or self._sample_index is None or not self._active_rows:
            return
        rows = np.asarray(self._active_rows, dtype=np.int32)
        self._sample_index[rows] += 1
        finished = self._sample_index[rows] >= self._lengths[rows]

        if finished.any():
            finished_rows = rows[finished]
            self._lengths[finished_rows] = 0
            self._sample_index[finished_rows] = 0
            for idx in finished_rows.tolist():
                row = int(idx)
                self._artists[row] = None
                self._deactivate_row(row)

    def remove(self, rows: Iterable[int]) -> None:
        if self._lengths is None or self._sample_index is None:
            return
        for idx in rows:
            row = int(idx)
            self._lengths[row]      = 0
            self._sample_index[row] = 0
            self._artists[row]      = None
            self._deactivate_row(row)

    def clear(self) -> None:
        if self._lengths is None or self._sample_index is None:
            return
        self._lengths.fill(0)
        self._sample_index.fill(0)
        self._cursor = 0
        self._active_rows.clear()
        if self._active_pos is not None:
            self._active_pos.fill(-1)
        for idx in range(self.capacity):
            self._artists[idx] = None

    # Matplotlib artist helpers ---------------------------------------------
    def get_artist(self, row: int) -> Any:       # noqa: D401
        return self._artists[row]

    def set_artist(self, row: int, artist: Any) -> None:
        self._artists[row] = artist


# --------------------------------------------------------------------------- #
# global runtime container
# --------------------------------------------------------------------------- #
@dataclass
class FlightState:
    frame     : int     = 0
    plane_pos : Vector3 = (0.0, 0.0, 0.0)
    plane_vel : Vector3 = (0.0, 0.0, 0.0)   # bogie fields removed


@dataclass
class EnvironmentState:
    wind: Vector3 = (0.0, 0.0, 0.0)
    gust: Vector3 = (0.0, 0.0, 0.0)
    turbulence: float = 0.0
    visibility_km: float = 20.0


@dataclass
class RuntimeState:
    active_bullets : ProjectileBuffer      = field(default_factory=ProjectileBuffer)
    active_rockets : ProjectileBuffer      = field(default_factory=ProjectileBuffer)
    active_bombs   : ProjectileBuffer      = field(default_factory=ProjectileBuffer)
    explosions     : list[ExplosionEvent] = field(default_factory=_new_explosions)
    parachutes     : list[ParachuteEvent] = field(default_factory=_new_parachutes)
    impacts        : list[ImpactEvent]     = field(default_factory=_new_impacts)
    debug_events   : list[DebugEvent]      = field(default_factory=_new_debug_events)
    flight         : FlightState           = field(default_factory=FlightState)
    environment    : EnvironmentState      = field(default_factory=EnvironmentState)


# single module-level instance
RUNTIME: RuntimeState = RuntimeState()

__all__ = [
    "Vector3",
    "ExplosionState",
    "ParachuteState",
    "ImpactEvent",
    "DebugEvent",
    "ProjectileBuffer",
    "FlightState",
    "EnvironmentState",
    "RuntimeState",
    "RUNTIME",
]
