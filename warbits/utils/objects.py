from __future__ import annotations

__all__: list[str] = []

# Sentinel that can be used across the code‑base where a unique “null /
# not‑set” value is preferable to ``None``.
class _Null:
    __slots__ = ()

    def __repr__(self) -> str:  # pragma: no cover
        return "<warbits.utils.objects.NULL>"

NULL = _Null()
