from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional, Tuple


class Panda3DNotInstalled(RuntimeError):
    """Raised when a Panda3D feature is requested but Panda3D is not available."""


@dataclass(frozen=True)
class Panda3DImportInfo:
    ok: bool
    error: Optional[str] = None
    hint: str = "Install with: pip install panda3d"


def is_panda3d_available() -> bool:
    try:
        import direct.showbase.ShowBase  # type: ignore[import-not-found]  # noqa: F401
        import panda3d.core  # type: ignore[import-not-found]  # noqa: F401

        return True
    except Exception:
        return False


def panda3d_import_info() -> Panda3DImportInfo:
    try:
        import direct.showbase.ShowBase  # type: ignore[import-not-found]  # noqa: F401
        import panda3d.core  # type: ignore[import-not-found]  # noqa: F401

        return Panda3DImportInfo(ok=True)
    except Exception as e:
        return Panda3DImportInfo(ok=False, error=str(e))


def require_panda3d() -> Tuple[Any, Any]:
    """Return (panda3d.core, ShowBase) or raise Panda3DNotInstalled.

    We return the modules rather than importing at top-level, so normal imports
    remain safe on machines without Panda3D.
    """
    try:
        import panda3d.core as p3d  # type: ignore[import-not-found]
        from direct.showbase.ShowBase import ShowBase  # type: ignore[import-not-found, reportMissingTypeStubs]

        return p3d, ShowBase
    except Exception as e:
        info = panda3d_import_info()
        raise Panda3DNotInstalled(f"Panda3D is not available: {e}\n\n{info.hint}\n") from e
