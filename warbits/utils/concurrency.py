"""
Thread-pool & process-pool helpers used across WarBits.

External deps: numpy, threadpoolctl
"""

from __future__ import annotations

import os
import platform
import ctypes
from multiprocessing import cpu_count, get_context, pool
from typing import Any

try:
    from threadpoolctl import threadpool_limits      # pip install threadpoolctl  # type: ignore
except Exception:  # optional dependency
    def threadpool_limits(*args: Any, **kwargs: Any) -> None:
        return None
import numpy as xp                                    # single public alias expected elsewhere

__all__ = [
    "xp",
    "use_all_cores",
    "cpu_pool",
    "detect_hardware",
]

# ─────────────────────────────────────────────────────────────────────────────
# Low-level: pin every BLAS / OpenMP runtime to *all* physical CPUs
# ─────────────────────────────────────────────────────────────────────────────
def _pin_blas_threads() -> None:
    n = cpu_count()
    for var in (
        "OMP_NUM_THREADS",
        "OPENBLAS_NUM_THREADS",
        "MKL_NUM_THREADS",
        "NUMEXPR_NUM_THREADS",
        "VECLIB_MAXIMUM_THREADS",
    ):
        os.environ.setdefault(var, str(n))
    try:
        threadpool_limits(limits=n)
    except Exception:
        pass


def _unpark_windows() -> None:
    if platform.system() != "Windows":
        return
    try:
        # Keep all logical processors awake
        _ = ctypes.windll.kernel32.SetThreadExecutionState(
            0x80000000 | 0x00000002  # ES_CONTINUOUS | ES_SYSTEM_REQUIRED
        )
    except Exception:
        pass


# ─────────────────────────────────────────────────────────────────────────────
# Public helpers
# ─────────────────────────────────────────────────────────────────────────────
def use_all_cores() -> None:        # noqa: D401
    """Pin every BLAS / OpenMP pool to *all* physical cores."""
    _pin_blas_threads()
    _unpark_windows()


# One lazy, fork-safe process pool — NUMBA-free / pure stdlib
_cpu_ctx = get_context("spawn")
_cpu_pool: pool.Pool | None = None


def cpu_pool() -> pool.Pool:
    """Return (and cache) a `multiprocessing.Pool` sized to all cores."""
    global _cpu_pool
    if _cpu_pool is None:
        _cpu_pool = _cpu_ctx.Pool(processes=cpu_count(), maxtasksperchild=128)
    return _cpu_pool


# ─────────────────────────────────────────────────────────────────────────────
# Hardware introspection
# ─────────────────────────────────────────────────────────────────────────────
def _total_ram_gb() -> int:
    try:
        sysconf = getattr(os, "sysconf", None)
        if callable(sysconf):
            pages = sysconf("SC_PHYS_PAGES")
            size = sysconf("SC_PAGE_SIZE")
        else:
            pages = size = 0
        if isinstance(pages, int) and isinstance(size, int):
            return int(pages * size / 1_073_741_824)
    except Exception:
        pass
    return 0


def detect_hardware() -> dict[str, Any]:
    """Return a dict with the most relevant HW capabilities for logging."""
    return {
        "cpus": cpu_count(),
        "ram_gb": _total_ram_gb(),
        "backend": "MKL"
        if xp.__config__.get_info("blas_mkl_info")  # type: ignore[attr-defined]
        else "OpenBLAS",
        "cuda": False,
        "platform": platform.platform(),
    }
