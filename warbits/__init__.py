from __future__ import annotations

import sys
from importlib import import_module as _import
from typing import TYPE_CHECKING, cast

# --------------------------------------------------------------------------- #
# Package version
# --------------------------------------------------------------------------- #
try:
    from importlib.metadata import version as _pkg_version  # Python ≥3.8
except ImportError:                                         # pragma: no cover
    from importlib_metadata import version as _pkg_version  # type: ignore

try:
    __version__: str = cast(str, _pkg_version("warbits"))
except Exception:                                           # pragma: no cover
    __version__ = "0.0.dev-local"

if TYPE_CHECKING:
    from . import config, data, logic, physics, scene, simlib, utils

__all__: list[str] = [
    "config",
    "data",
    "physics",
    "scene",
    "logic",
    "simlib",
    "utils",
    "__version__",
    "main",
]

_LAZY_MODULES = {"config", "data", "physics", "scene", "logic", "simlib", "utils"}


def __getattr__(name: str) -> object:
    if name in _LAZY_MODULES:
        module = _import(f"warbits.{name}")
        globals()[name] = module
        return module
    raise AttributeError(f"module 'warbits' has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted(set(__all__))

# --------------------------------------------------------------------------- #
# CLI trampoline:  python -m warbits  ->  warbits.cli.warb​its_cli:main()
# --------------------------------------------------------------------------- #
def main(argv: list[str] | None = None) -> None:            # pragma: no cover
    if argv is None:
        argv = sys.argv[1:]

    cli_mod = _import("warbits.cli.warbits_cli")
    cli_mod.main(argv)  # type: ignore[attr-defined]
