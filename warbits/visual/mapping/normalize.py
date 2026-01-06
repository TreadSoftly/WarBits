"""String normalization helpers for matching IDs to blueprints.

We don't try to be fancy NLP here.
We want something deterministic, cheap, and "good enough" so humans can
review/override mappings instead of hand-typing everything.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable, Iterator, Sequence

_RE_NON_ALNUM = re.compile(r"[^a-z0-9]+")
_RE_WS = re.compile(r"\s+")


def normalize_text(s: str) -> str:
    """Lowercase and replace punctuation with spaces."""
    s = s.strip().lower()
    # Common separators -> space
    s = s.replace("/", " ").replace("_", " ").replace("-", " ")
    s = _RE_NON_ALNUM.sub(" ", s)
    s = _RE_WS.sub(" ", s).strip()
    return s


def tokenize(s: str) -> list[str]:
    """Tokenize into a stable list of lowercase alphanumeric tokens."""
    n = normalize_text(s)
    if not n:
        return []
    toks = n.split(" ")

    # Add joined variants for patterns like "f 15" -> "f15"
    joined: list[str] = []
    for a, b in zip(toks, toks[1:]):
        if len(a) == 1 and b.isdigit():
            joined.append(f"{a}{b}")
        if a.isdigit() and len(b) == 1:
            joined.append(f"{a}{b}")
    # Keep deterministic ordering
    return toks + joined


def token_set(s: str) -> set[str]:
    return set(tokenize(s))


def jaccard(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    inter = len(a & b)
    union = len(a | b)
    return inter / float(union)


@dataclass(frozen=True)
class NameKey:
    """Precomputed token set for a name-like string."""

    raw: str
    tokens: frozenset[str]

    @staticmethod
    def from_str(s: str) -> "NameKey":
        return NameKey(raw=s, tokens=frozenset(token_set(s)))


def iter_best_matches(
    queries: Sequence[NameKey],
    candidates: Sequence[NameKey],
    *,
    min_score: float = 0.25,
    top_k: int = 3,
) -> Iterator[tuple[NameKey, list[tuple[NameKey, float]]]]:
    """Yield best matches for each query based on Jaccard similarity."""

    for q in queries:
        scored: list[tuple[NameKey, float]] = []
        for c in candidates:
            score = jaccard(set(q.tokens), set(c.tokens))
            if score >= min_score:
                scored.append((c, score))
        scored.sort(key=lambda t: t[1], reverse=True)
        yield q, scored[:top_k]


def canonical_key(s: str) -> NameKey:
    """Convenience wrapper used by tools/tests."""

    return NameKey.from_str(s)
