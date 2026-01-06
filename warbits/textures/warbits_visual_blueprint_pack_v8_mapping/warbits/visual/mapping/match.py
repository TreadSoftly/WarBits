"""Heuristic matching between WarBits IDs and blueprint IDs.

This is used to generate *suggestions*:
  - You ingest a bunch of mesh blueprints.
  - You have a list of vehicle/weapon IDs in your data store.
  - We try to connect them automatically.

Humans remain the authority: you can accept, override, or ignore suggestions.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

from .normalize import NameKey, iter_best_matches, normalize_text


@dataclass(frozen=True)
class MatchSuggestion:
    entity_id: str
    blueprint_id: str
    score: float


def _strip_prefixes(s: str, prefixes: Sequence[str]) -> str:
    for p in prefixes:
        if s.startswith(p):
            return s[len(p) :]
    return s


def suggest_bindings(
    entity_ids: Sequence[str],
    blueprint_ids: Sequence[str],
    *,
    entity_prefixes: Sequence[str] = ("vehicle:", "weapon:", "warhead:", "sensor:"),
    blueprint_prefixes: Sequence[str] = ("mesh:", "bp:", "blueprint:"),
    min_score: float = 0.33,
    top_k: int = 1,
) -> list[MatchSuggestion]:
    """Return 0..N mapping suggestions.

    The output is sorted by score descending and is deterministic.
    """

    qkeys = [NameKey.from_str(_strip_prefixes(normalize_text(e), entity_prefixes)) for e in entity_ids]
    ckeys = [NameKey.from_str(_strip_prefixes(normalize_text(b), blueprint_prefixes)) for b in blueprint_ids]

    # Map back to original IDs
    key_to_entity = {k: e for k, e in zip(qkeys, entity_ids)}
    key_to_bp = {k: b for k, b in zip(ckeys, blueprint_ids)}

    out: list[MatchSuggestion] = []
    for q, matches in iter_best_matches(qkeys, ckeys, min_score=min_score, top_k=max(1, top_k)):
        if not matches:
            continue
        # Top-k suggestions
        for c, score in matches[:top_k]:
            out.append(MatchSuggestion(entity_id=key_to_entity[q], blueprint_id=key_to_bp[c], score=score))

    out.sort(key=lambda m: (-m.score, m.entity_id, m.blueprint_id))
    return out

# Backwards/CLI-friendly aliases
Suggestion = MatchSuggestion


def best_matches(
    spec_ids: Sequence[str],
    blueprint_ids: Sequence[str],
    *,
    min_score: float = 0.33,
    top_k: int = 1,
) -> list[Suggestion]:
    """Alias for suggest_bindings (older name used in tools/tests)."""

    return [
        Suggestion(entity_id=s.entity_id, blueprint_id=s.blueprint_id, score=s.score)
        for s in suggest_bindings(spec_ids, blueprint_ids, min_score=min_score, top_k=top_k)
    ]
