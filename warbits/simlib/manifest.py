"""Run manifest helpers ("black box flight recorder").

A manifest is a JSON artifact you write every run (or every headless batch) that captures:
- config dump
- seed(s)
- data build hashes (vehicles/weapons/warheads/etc.)
- version strings (optional)
- machine + python + numpy info
- basic timing summaries

This makes bug reports and determinism debugging dramatically easier.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, Iterable, Optional
import hashlib
import os
import platform
import sys
import time

try:
    import numpy as np  # type: ignore
except Exception:  # pragma: no cover
    np = None  # type: ignore

from .serialization import json_dump_file, to_jsonable


def sha256_file(path: str | Path) -> str:
    p = Path(path)
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_files(paths: Iterable[str | Path]) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for p in paths:
        pp = Path(p)
        if pp.exists() and pp.is_file():
            out[str(pp)] = sha256_file(pp)
    return out


@dataclass
class RunManifest:
    created_utc: str
    duration_s: float
    version: str
    seed: str | int
    config: Dict[str, Any]
    data_hashes: Dict[str, str]
    system: Dict[str, Any]
    timings: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return to_jsonable(asdict(self))  # type: ignore[arg-type]


def collect_system_info() -> Dict[str, Any]:
    info: Dict[str, Any] = {
        "platform": platform.platform(),
        "python": sys.version,
        "python_executable": sys.executable,
        "cpu_count": os.cpu_count(),
    }
    if np is not None:
        info["numpy_version"] = np.__version__
    return info


def build_manifest(
    *,
    seed: str | int,
    config: Dict[str, Any],
    data_files_to_hash: Iterable[str | Path] = (),
    version: Optional[str] = None,
    timings: Optional[Dict[str, Any]] = None,
    t_start: Optional[float] = None,
) -> RunManifest:
    v = version or os.environ.get("WARBITS_VERSION", "unknown")
    start = float(t_start) if t_start is not None else time.time()
    duration = time.time() - start
    created = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    return RunManifest(
        created_utc=created,
        duration_s=float(duration),
        version=str(v),
        seed=seed,
        config=dict(config),
        data_hashes=sha256_files(data_files_to_hash),
        system=collect_system_info(),
        timings=dict(timings or {}),
    )


def write_manifest(path: str | Path, manifest: RunManifest) -> None:
    json_dump_file(path, manifest.to_dict(), indent=2)
