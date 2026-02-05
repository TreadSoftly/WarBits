"""Deterministic RNG utilities.

Goals:
- One RNG source for sim logic (no hidden global random state).
- Deterministic seeding from ints/strings/bytes.
- Deterministic *substreams* via `split(label)` that do NOT depend on draw order.

Implementation notes:
- Uses numpy.random.Generator with PCG64 under the hood.
- `DeterministicRNG` is *stateful*: repeated draws advance the stream.
- `split(label)` derives a brand-new seed from (root_seed, stream_path, label),
  so a child stream is stable even if the parent has drawn random numbers.

Cross-machine note:
- Floating point math can differ slightly across hardware/OS.
- RNG outputs are stable for a given numpy version and seed.
- Pin dependency versions for strong reproducibility.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Any, Iterable, Optional, cast

import numpy as np


def _seed_bytes(seed: int | str | bytes, *, context: str = "warbits") -> bytes:
    if isinstance(seed, bytes):
        raw = seed
    elif isinstance(seed, str):
        raw = seed.encode("utf-8")
    elif isinstance(seed, int):
        raw = seed.to_bytes(16, byteorder="little", signed=True)
    else:
        raw = repr(seed).encode("utf-8")

    return context.encode("utf-8") + b"\0" + raw


def stable_seed_u64(seed: int | str | bytes, *, context: str = "warbits") -> int:
    """Map a seed input to a stable unsigned 64-bit integer."""
    h = hashlib.blake2b(_seed_bytes(seed, context=context), digest_size=8).digest()
    return int.from_bytes(h, byteorder="little", signed=False)


def _derive_u64(parent_seed_u64: int, stream: str, label: str) -> int:
    msg = f"{parent_seed_u64}:{stream}:{label}".encode("utf-8")
    h = hashlib.blake2b(msg, digest_size=8).digest()
    return int.from_bytes(h, byteorder="little", signed=False)


@dataclass
class DeterministicRNG:
    """Stateful deterministic RNG stream."""

    root_seed_u64: int
    stream: str = "root"
    _gen: np.random.Generator = field(init=False, repr=False)

    def __post_init__(self) -> None:
        if not (0 <= int(self.root_seed_u64) < 2**64):
            raise ValueError("root_seed_u64 must be uint64")
        self._gen = np.random.default_rng(int(self.root_seed_u64))

    @classmethod
    def from_seed(cls, seed: int | str | bytes, *, context: str = "warbits") -> "DeterministicRNG":
        return cls(stable_seed_u64(seed, context=context))

    def split(self, label: str) -> "DeterministicRNG":
        """Create a deterministic child stream independent of draw order."""
        child_seed = _derive_u64(int(self.root_seed_u64), self.stream, str(label))
        child_stream = f"{self.stream}/{label}"
        return DeterministicRNG(child_seed, stream=child_stream)

    def generator(self) -> np.random.Generator:
        return self._gen

    # Convenience wrappers (advance the stream)

    def uniform(self, low: float = 0.0, high: float = 1.0, *, size: Optional[int | tuple[int, ...]] = None) -> Any:
        return self._gen.uniform(low, high, size=size)

    def normal(self, loc: float = 0.0, scale: float = 1.0, *, size: Optional[int | tuple[int, ...]] = None) -> Any:
        return self._gen.normal(loc, scale, size=size)

    def integers(self, low: int, high: Optional[int] = None, *, size: Optional[int | tuple[int, ...]] = None) -> Any:
        gen = cast(Any, self._gen)
        return gen.integers(low, high=high, size=size)

    def choice(
        self,
        a: int | Iterable[Any],
        *,
        size: Optional[int | tuple[int, ...]] = None,
        replace: bool = True,
        p: Any = None,
    ) -> Any:
        gen = cast(Any, self._gen)
        if size is None:
            return gen.choice(a, replace=replace, p=p)
        return gen.choice(a, size=size, replace=replace, p=p)

    def shuffle_inplace(self, x: Any) -> None:
        self._gen.shuffle(x)

    def random_u64(self) -> int:
        gen = cast(Any, self._gen)
        return int(gen.integers(0, 2**64, dtype=np.uint64))
