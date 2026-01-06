from __future__ import annotations

from typing import TYPE_CHECKING

from .base import RendererAdapter

if TYPE_CHECKING:
    from .matplotlib_renderer import MatplotlibRenderer


def __getattr__(name: str) -> object:
    if name == "MatplotlibRenderer":
        from .matplotlib_renderer import MatplotlibRenderer

        return MatplotlibRenderer
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = ["RendererAdapter", "MatplotlibRenderer"]
