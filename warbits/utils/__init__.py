# ── warbits/utils/__init__.py ────────────────────────────────────────────────
from __future__ import annotations

import sys
import types
from importlib import import_module
from types import ModuleType

# --------------------------------------------------------------------------- #
# Public sub-modules (lazy-imported, re-exported for `from … import *`)
# --------------------------------------------------------------------------- #
__all__: list[str] = ["concurrency", "math_tools", "objects"]


def __getattr__(name: str) -> ModuleType:                     # pragma: no cover
    fq_name = f"{__name__}.{name}"

    # already imported?
    if fq_name in sys.modules:
        return sys.modules[fq_name]

    try:
        mod = import_module(fq_name)
    except ModuleNotFoundError:
        mod = types.ModuleType(fq_name)  # harmless placeholder

    sys.modules[fq_name] = mod
    return mod


# Import helpers immediately so `from warbits.utils import math_tools` is fast.
from . import concurrency, math_tools, objects  # noqa: E402  (intentional)

# --------------------------------------------------------------------------- #
# Legacy placeholder names that old code may still reference
# --------------------------------------------------------------------------- #
_missing = [
    "bools",
    "dates",
    "enum",
    "lists",
    "math",
    "dicts",
    "dicts.chained_dict",
    "dicts.helpers",
    "dicts.limited_dict",
]

_pkg = __name__
for _m in _missing:
    fq = f"{_pkg}.{_m}"
    if fq not in sys.modules:
        sys.modules[fq] = types.ModuleType(fq)
