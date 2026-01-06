from collections.abc import Mapping
from importlib import import_module as _import
from types import ModuleType
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from . import settings, style

__all__ = ["settings", "style", "get"]

_SECTIONS: Mapping[str, str] = {
    "settings": "warbits.config.settings",
    "style": "warbits.config.style",
}


def _load_section(name: str) -> ModuleType:
    module = _import(_SECTIONS[name])
    globals()[name] = module
    return module


def __getattr__(name: str) -> Any:
    if name in _SECTIONS:
        return _load_section(name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def get(dotted_path: str) -> Any:
    parts = dotted_path.split(".")
    try:
        obj: Any = _load_section(parts[0])
    except KeyError as exc:
        raise KeyError(
            f"Unknown config section '{parts[0]}'. "
            f"Valid toplevel keys: {', '.join(_SECTIONS)}"
        ) from exc

    for chunk in parts[1:]:
        obj = getattr(obj, chunk)
    return obj
