from __future__ import annotations

import dataclasses
import hashlib
from typing import Any, Optional, Sequence, Tuple, Union, cast

import numpy as np


def stable_hash64(*parts: Any, salt: bytes = b"warbits.simlib.ai") -> int:
    """Compute a stable 64-bit unsigned hash.

    Why this exists:
    - Python's built-in `hash()` is randomized between processes.
    - For deterministic simulation/AI, we need a stable hash.

    Inputs:
    - parts: anything reasonably representable as bytes/str/int/float/bool/None.

    Returns:
    - uint64 in python int range.
    """
    h = hashlib.blake2b(digest_size=8)
    h.update(salt)
    for p in parts:
        if p is None:
            h.update(b"\x00")
        elif isinstance(p, (bytes, bytearray)):
            h.update(b"b:")
            h.update(bytes(p))
        elif isinstance(p, str):
            h.update(b"s:")
            h.update(p.encode("utf-8", errors="strict"))
        elif isinstance(p, bool):
            h.update(b"t:" + (b"1" if p else b"0"))
        elif isinstance(p, int):
            h.update(b"i:")
            h.update(int(p).to_bytes(16, "little", signed=True))
        elif isinstance(p, float):
            # IEEE754 stable packing via numpy
            h.update(b"f:")
            h.update(np.float64(p).tobytes())
        else:
            # Fallback: deterministic repr (best-effort; avoid for critical seeds)
            h.update(b"r:")
            h.update(repr(p).encode("utf-8", errors="replace"))
        h.update(b"|")
    return int.from_bytes(h.digest(), "little", signed=False)


@dataclasses.dataclass(frozen=True)
class DeterministicRNG:
    """A small deterministic RNG wrapper around numpy's Generator.

    Goals:
    - explicit seed ownership
    - stable substreams (fork/spawn) without depending on Python hash randomization
    - convenience helpers for common AI needs

    Notes on determinism across machines:
    - numpy's bit generators are deterministic across platforms for the same version.
    - across numpy versions, exact sequences are usually stable but not guaranteed.
      For strict long-term determinism, pin numpy in your lockfile.

    This wrapper uses PCG64 by default.
    """

    seed_u64: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "seed_u64", int(self.seed_u64) & ((1 << 64) - 1))

    def _gen(self) -> np.random.Generator:
        bitgen = np.random.PCG64(self.seed_u64)
        return np.random.Generator(bitgen)

    def fork(self, *key_parts: Any) -> "DeterministicRNG":
        """Create a deterministic substream based on the current seed + key."""
        child_seed = stable_hash64(self.seed_u64, *key_parts)
        return DeterministicRNG(child_seed)

    # ---- primitives ----
    def random(self) -> float:
        return float(self._gen().random())

    def uniform(self, low: float, high: float, size: Optional[Union[int, Tuple[int, ...]]] = None):
        return self._gen().uniform(low=low, high=high, size=size)

    def normal(self, mean: float = 0.0, std: float = 1.0, size: Optional[Union[int, Tuple[int, ...]]] = None):
        return self._gen().normal(loc=mean, scale=std, size=size)

    def integers(self, low: int, high: Optional[int] = None, size: Optional[Union[int, Tuple[int, ...]]] = None):
        gen = cast(Any, self._gen())
        return gen.integers(low=low, high=high, size=size)

    def choice(
        self,
        seq: Sequence[Any],
        p: Optional[Sequence[float]] = None,
    ) -> Any:
        if len(seq) == 0:
            raise ValueError("choice() cannot choose from an empty sequence")
        idx = int(self._gen().choice(len(seq), p=p))
        return seq[idx]

    def shuffle_in_place(self, items: list[Any]) -> None:
        self._gen().shuffle(items)

    def weighted_index(self, weights: Sequence[float]) -> int:
        """Return an index sampled proportionally to weights (weights can be unnormalized)."""
        if len(weights) == 0:
            raise ValueError("weighted_index() requires at least one weight")
        w = np.asarray(weights, dtype=np.float64)
        if np.any(w < 0):
            raise ValueError("weighted_index() does not allow negative weights")
        s = float(np.sum(w))
        if not np.isfinite(s) or s <= 0.0:
            # fall back to uniform
            return int(self.integers(0, len(weights)))
        p = (w / s).tolist()
        return int(self._gen().choice(len(weights), p=p))

    def bernoulli(self, p: float) -> bool:
        if p <= 0.0:
            return False
        if p >= 1.0:
            return True
        return bool(self._gen().random() < p)

    def reseed(self, seed_u64: int) -> "DeterministicRNG":
        return DeterministicRNG(seed_u64)
