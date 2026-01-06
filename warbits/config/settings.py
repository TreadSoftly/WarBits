# pyright: reportMissingTypeStubs=false, reportUnknownMemberType=false, reportUnusedImport=false, reportUnusedFunction=false, reportUnusedVariable=false
# ── warbits/config/settings.py ─────────────────────────────────────────────
from __future__ import annotations

import os
import warnings
from typing import TYPE_CHECKING, Any, Tuple, cast


# ── typing-only heavy imports (silenced if stubs are missing) ──────────────
if TYPE_CHECKING:
    from matplotlib.figure import Figure
    from mpl_toolkits.mplot3d import Axes3D        # type: ignore[import-not-found]
else:
    Figure = Any                                   # type: ignore[assignment]
    Axes3D = Any                                   # type: ignore[assignment]

# ─────────────────────── screen / DPI helpers ──────────────────────────────
def _read_env_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None:
        return default
    try:
        value = int(raw)
    except (TypeError, ValueError):
        warnings.warn(f"Ignoring invalid {name}={raw!r}; using {default}")
        return default
    if value <= 0:
        warnings.warn(f"Ignoring non-positive {name}={raw!r}; using {default}")
        return default
    return value


def _read_env_int_signed(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except (TypeError, ValueError):
        warnings.warn(f"Ignoring invalid {name}={raw!r}; using {default}")
        return default


def _read_env_int_nonneg(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None:
        return default
    try:
        value = int(raw)
    except (TypeError, ValueError):
        warnings.warn(f"Ignoring invalid {name}={raw!r}; using {default}")
        return default
    if value < 0:
        warnings.warn(f"Ignoring negative {name}={raw!r}; using {default}")
        return default
    return value


def _read_env_int_optional(name: str) -> int | None:
    raw = os.environ.get(name)
    if raw is None:
        return None
    try:
        return int(raw)
    except (TypeError, ValueError):
        warnings.warn(f"Ignoring invalid {name}={raw!r}; using default")
    return None


def _read_env_float(name: str, default: float) -> float:
    raw = os.environ.get(name)
    if raw is None:
        return default
    try:
        value = float(raw)
    except (TypeError, ValueError):
        warnings.warn(f"Ignoring invalid {name}={raw!r}; using {default}")
        return default
    if value <= 0:
        warnings.warn(f"Ignoring non-positive {name}={raw!r}; using {default}")
        return default
    return value


def _read_env_float_nonneg(name: str, default: float) -> float:
    raw = os.environ.get(name)
    if raw is None:
        return default
    try:
        value = float(raw)
    except (TypeError, ValueError):
        warnings.warn(f"Ignoring invalid {name}={raw!r}; using {default}")
        return default
    if value < 0:
        warnings.warn(f"Ignoring negative {name}={raw!r}; using {default}")
        return default
    return value


def _read_env_float_signed(name: str, default: float) -> float:
    raw = os.environ.get(name)
    if raw is None:
        return default
    try:
        return float(raw)
    except (TypeError, ValueError):
        warnings.warn(f"Ignoring invalid {name}={raw!r}; using {default}")
        return default


def _read_env_bool(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() not in {"0", "false", "off", "no", "n"}


def _read_env_str(name: str, default: str) -> str:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip() or default


def _coerce_int_optional(value: object) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            return None
    try:
        return int(cast(Any, value))
    except (TypeError, ValueError):
        return None


def _detect_ram_gb() -> float:
    if os.name == "nt":
        try:
            import ctypes

            class _MemoryStatus(ctypes.Structure):
                _fields_ = [
                    ("dwLength", ctypes.c_ulong),
                    ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong),
                    ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong),
                    ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong),
                    ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
                ]

            status = _MemoryStatus()
            status.dwLength = ctypes.sizeof(status)
            if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
                return float(status.ullTotalPhys) / (1024.0 ** 3)
        except Exception:
            return 0.0

    sysconf = getattr(os, "sysconf", None)
    if callable(sysconf):
        try:
            page_size_raw = sysconf("SC_PAGE_SIZE")
            phys_pages_raw = sysconf("SC_PHYS_PAGES")
        except (OSError, ValueError, TypeError):
            return 0.0
        page_size = _coerce_int_optional(page_size_raw)
        phys_pages = _coerce_int_optional(phys_pages_raw)
        if page_size is None or phys_pages is None:
            return 0.0
        total = page_size * phys_pages
        if total > 0:
            return float(total) / (1024.0 ** 3)
    return 0.0


def _detect_screen(*, allow_tk: bool) -> Tuple[int, int]:
    try:
        w = _read_env_int("WARBITS_SCREEN_WIDTH", 0)
        h = _read_env_int("WARBITS_SCREEN_HEIGHT", 0)
        if w > 0 and h > 0:
            return w, h
    except Exception:
        pass

    if os.name == "nt":
        try:
            import ctypes

            user32 = ctypes.windll.user32
            w_raw = user32.GetSystemMetrics(0)
            h_raw = user32.GetSystemMetrics(1)
            if not isinstance(w_raw, (int, float)) or not isinstance(h_raw, (int, float)):
                raise TypeError("GetSystemMetrics returned non-numeric values")
            w = int(w_raw)
            h = int(h_raw)
            if w > 0 and h > 0:
                return w, h
        except Exception as exc:
            warnings.warn(f"Could not query screen size via WinAPI: {exc!s}")
        return 1920, 1080

    if not allow_tk:
        return 1920, 1080

    try:                                           # lightweight Tk probe
        import tkinter as _tk
        root = _tk.Tk()
        root.withdraw()
        w = root.winfo_screenwidth()
        h = root.winfo_screenheight()
        root.destroy()
        if isinstance(w, (int, float)) and isinstance(h, (int, float)) and w and h:
            return int(w), int(h)
    except Exception as exc:
        warnings.warn(f"Could not query screen size via Tkinter: {exc!s}")

    return 1920, 1080

_SCREEN_DETECTED_TK = False
SCREEN_WIDTH_PX, SCREEN_HEIGHT_PX = _detect_screen(allow_tk=False)
RAM_GB = _detect_ram_gb()
PERF_MODE = _read_env_bool("WARBITS_PERF_MODE", False)
_PERF_CANVAS_MAX_PIXELS = _read_env_int_nonneg("WARBITS_PERF_CANVAS_MAX_PIXELS", 2_200_000)
DEFAULT_FIG_DPI = _read_env_int("WARBITS_DEFAULT_DPI", 40)
_canvas_max_pixels = _read_env_int_nonneg("WARBITS_CANVAS_MAX_PIXELS", 3_000_000)
if PERF_MODE and _PERF_CANVAS_MAX_PIXELS > 0:
    _canvas_max_pixels = min(_canvas_max_pixels, _PERF_CANVAS_MAX_PIXELS)
CANVAS_MAX_PIXELS = _canvas_max_pixels
_CANVAS_SCALE_RAW = os.environ.get("WARBITS_CANVAS_SCALE")

def _compute_canvas_scale(screen_w: int, screen_h: int) -> float:
    scale = _read_env_float("WARBITS_CANVAS_SCALE", 1.0)
    if _CANVAS_SCALE_RAW is None and CANVAS_MAX_PIXELS > 0:
        screen_pixels = max(1, screen_w * screen_h)
        auto_scale = (CANVAS_MAX_PIXELS / screen_pixels) ** 0.5
        if auto_scale < 1.0:
            scale = auto_scale
    return scale


_canvas_scale = _compute_canvas_scale(SCREEN_WIDTH_PX, SCREEN_HEIGHT_PX)
CANVAS_SCALE = _canvas_scale

FULLSCREEN = _read_env_bool("WARBITS_FULLSCREEN", True)

FIGSIZE_INCHES = (
    (SCREEN_WIDTH_PX * CANVAS_SCALE) / DEFAULT_FIG_DPI,
    (SCREEN_HEIGHT_PX * CANVAS_SCALE) / DEFAULT_FIG_DPI,
)


def _refresh_screen() -> None:
    global SCREEN_WIDTH_PX, SCREEN_HEIGHT_PX, CANVAS_SCALE, FIGSIZE_INCHES, _canvas_scale, _SCREEN_DETECTED_TK
    if os.name == "nt" or _SCREEN_DETECTED_TK:
        return
    w, h = _detect_screen(allow_tk=True)
    _SCREEN_DETECTED_TK = True
    if w <= 0 or h <= 0:
        return
    if w == SCREEN_WIDTH_PX and h == SCREEN_HEIGHT_PX:
        return
    SCREEN_WIDTH_PX, SCREEN_HEIGHT_PX = w, h
    _canvas_scale = _compute_canvas_scale(w, h)
    CANVAS_SCALE = _canvas_scale
    FIGSIZE_INCHES = (
        (SCREEN_WIDTH_PX * CANVAS_SCALE) / DEFAULT_FIG_DPI,
        (SCREEN_HEIGHT_PX * CANVAS_SCALE) / DEFAULT_FIG_DPI,
    )

# quality / performance tuning (auto unless overridden)
def _auto_quality() -> str:
    cpus = os.cpu_count() or 1
    ram_gb = RAM_GB
    if ram_gb > 0.0:
        if cpus >= 12 and ram_gb >= 24.0:
            return "high"
        if cpus >= 8 and ram_gb >= 16.0:
            return "high"
        if cpus >= 6 and ram_gb >= 12.0:
            return "medium"
        if cpus >= 4 and ram_gb >= 8.0:
            return "medium"
        return "low"
    if cpus >= 12:
        return "high"
    if cpus >= 6:
        return "medium"
    return "low"


_QUALITY_RAW = _read_env_str("WARBITS_QUALITY", "auto").lower()
_QUALITY = _auto_quality() if _QUALITY_RAW == "auto" else _QUALITY_RAW
_QUALITY_LEVEL = {"low": 1, "medium": 2, "med": 2, "high": 3}.get(_QUALITY, 2)
_DETAIL_SCALE = {1: 0.60, 2: 0.80, 3: 1.00}[_QUALITY_LEVEL]

AUTO_MAX_PERF = _read_env_bool("WARBITS_AUTO_PERF", _QUALITY_LEVEL >= 2)
TERRAIN_STEP = _read_env_int("WARBITS_TERRAIN_STEP", max(60, int(300 * _DETAIL_SCALE)))
TERRAIN_RCOUNT = _read_env_int("WARBITS_TERRAIN_RCOUNT", min(30, TERRAIN_STEP))
TERRAIN_CCOUNT = _read_env_int("WARBITS_TERRAIN_CCOUNT", min(30, TERRAIN_STEP))
TERRAIN_SHADE = _read_env_bool("WARBITS_TERRAIN_SHADE", _QUALITY_LEVEL >= 3)
TERRAIN_ANTIALIASED = _read_env_bool("WARBITS_TERRAIN_ANTIALIASED", _QUALITY_LEVEL >= 3)
TERRAIN_ALPHA = _read_env_float("WARBITS_TERRAIN_ALPHA", 1.0 if _QUALITY_LEVEL < 3 else 0.25)
_TERRAIN_XMIN_BASE = float(_read_env_int_signed("WARBITS_TERRAIN_XMIN", 0))
_TERRAIN_XMAX_BASE = float(_read_env_int_signed("WARBITS_TERRAIN_XMAX", 18_500))
_TERRAIN_YMIN_BASE = float(_read_env_int_signed("WARBITS_TERRAIN_YMIN", 4_000))
_TERRAIN_YMAX_BASE = float(_read_env_int_signed("WARBITS_TERRAIN_YMAX", 9_300))
TERRAIN_ZMIN = float(_read_env_int("WARBITS_TERRAIN_ZMIN", 0))
TERRAIN_ZMAX = float(_read_env_int("WARBITS_TERRAIN_ZMAX", 15_000))
TERRAIN_FIT_SCREEN = _read_env_bool("WARBITS_TERRAIN_FIT_SCREEN", True)
TERRAIN_FORCE_SQUARE = _read_env_bool("WARBITS_TERRAIN_FORCE_SQUARE", True)
TERRAIN_SIZE = float(_read_env_int("WARBITS_TERRAIN_SIZE", 80_000))
TERRAIN_PROFILE = _read_env_str("WARBITS_TERRAIN_PROFILE", "auto").lower()
TERRAIN_LOCK_LOD = _read_env_bool("WARBITS_TERRAIN_LOCK_LOD", True)


def _fit_terrain_bounds_to_screen(
    xmin: float,
    xmax: float,
    ymin: float,
    ymax: float,
    screen_w: int,
    screen_h: int,
) -> tuple[float, float, float, float]:
    if screen_w <= 0 or screen_h <= 0:
        return xmin, xmax, ymin, ymax
    span_x = xmax - xmin
    span_y = ymax - ymin
    if span_x <= 0 or span_y <= 0:
        return xmin, xmax, ymin, ymax
    screen_ratio = float(screen_w) / float(screen_h)
    terrain_ratio = span_x / span_y
    if abs(terrain_ratio - screen_ratio) < 1e-6:
        return xmin, xmax, ymin, ymax
    if terrain_ratio > screen_ratio:
        target_span_y = span_x / screen_ratio
        pad = (target_span_y - span_y) / 2.0
        ymin -= pad
        ymax += pad
    else:
        target_span_x = span_y * screen_ratio
        pad = (target_span_x - span_x) / 2.0
        xmin -= pad
        xmax += pad
    return xmin, xmax, ymin, ymax


def _fit_terrain_bounds_to_square(
    xmin: float,
    xmax: float,
    ymin: float,
    ymax: float,
    size: float | None,
) -> tuple[float, float, float, float]:
    span_x = xmax - xmin
    span_y = ymax - ymin
    if span_x <= 0 or span_y <= 0:
        return xmin, xmax, ymin, ymax
    target_span = max(span_x, span_y)
    if size is not None:
        size_value = float(size)
        if size_value > 0.0:
            target_span = size_value
    cx = (xmin + xmax) / 2.0
    cy = (ymin + ymax) / 2.0
    half = target_span / 2.0
    return cx - half, cx + half, cy - half, cy + half


if TERRAIN_FIT_SCREEN:
    _terrain_bounds = _fit_terrain_bounds_to_screen(
        _TERRAIN_XMIN_BASE,
        _TERRAIN_XMAX_BASE,
        _TERRAIN_YMIN_BASE,
        _TERRAIN_YMAX_BASE,
        SCREEN_WIDTH_PX,
        SCREEN_HEIGHT_PX,
    )
else:
    _terrain_bounds = (
        _TERRAIN_XMIN_BASE,
        _TERRAIN_XMAX_BASE,
        _TERRAIN_YMIN_BASE,
        _TERRAIN_YMAX_BASE,
    )
if TERRAIN_FORCE_SQUARE:
    _terrain_bounds = _fit_terrain_bounds_to_square(
        _terrain_bounds[0],
        _terrain_bounds[1],
        _terrain_bounds[2],
        _terrain_bounds[3],
        TERRAIN_SIZE,
    )
TERRAIN_XMIN, TERRAIN_XMAX, TERRAIN_YMIN, TERRAIN_YMAX = _terrain_bounds
_SCENE_XMIN_ENV = _read_env_int_optional("WARBITS_SCENE_XMIN")
_SCENE_XMAX_ENV = _read_env_int_optional("WARBITS_SCENE_XMAX")
_SCENE_YMIN_ENV = _read_env_int_optional("WARBITS_SCENE_YMIN")
_SCENE_YMAX_ENV = _read_env_int_optional("WARBITS_SCENE_YMAX")
SCENE_FORCE_SQUARE = _read_env_bool("WARBITS_SCENE_FORCE_SQUARE", True)
_SCENE_SIZE_ENV = _read_env_int_optional("WARBITS_SCENE_SIZE")
_SCENE_SPAN_X_BASE = max(1.0, _TERRAIN_XMAX_BASE - _TERRAIN_XMIN_BASE)
_SCENE_SPAN_Y_BASE = max(1.0, _TERRAIN_YMAX_BASE - _TERRAIN_YMIN_BASE)
_SCENE_SIZE_DEFAULT = max(_SCENE_SPAN_X_BASE, _SCENE_SPAN_Y_BASE) * 1.0
SCENE_SIZE = float(_SCENE_SIZE_ENV) if _SCENE_SIZE_ENV is not None else _SCENE_SIZE_DEFAULT
scene_xmin = float(_SCENE_XMIN_ENV) if _SCENE_XMIN_ENV is not None else _TERRAIN_XMIN_BASE
scene_xmax = float(_SCENE_XMAX_ENV) if _SCENE_XMAX_ENV is not None else _TERRAIN_XMAX_BASE
scene_ymin = float(_SCENE_YMIN_ENV) if _SCENE_YMIN_ENV is not None else _TERRAIN_YMIN_BASE
scene_ymax = float(_SCENE_YMAX_ENV) if _SCENE_YMAX_ENV is not None else _TERRAIN_YMAX_BASE
if SCENE_FORCE_SQUARE:
    _scene_bounds = _fit_terrain_bounds_to_square(
        scene_xmin,
        scene_xmax,
        scene_ymin,
        scene_ymax,
        SCENE_SIZE,
    )
    scene_xmin, scene_xmax, scene_ymin, scene_ymax = _scene_bounds
SCENE_XMIN = scene_xmin
SCENE_XMAX = scene_xmax
SCENE_YMIN = scene_ymin
SCENE_YMAX = scene_ymax
FLIGHT_TERRAIN_CLEARANCE = _read_env_float("WARBITS_FLIGHT_TERRAIN_CLEARANCE", 300.0)
BOGIE_SCRIPTED_HIT = _read_env_bool("WARBITS_BOGIE_SCRIPTED_HIT", False)
AIM_ASSIST = _read_env_bool("WARBITS_AIM_ASSIST", True)
VISUAL_SCALE = _read_env_float("WARBITS_VISUAL_SCALE", 1.0)
MARKER_SCALE = _read_env_float("WARBITS_MARKER_SCALE", 1.0)
SPHERE_LAT = _read_env_int("WARBITS_SPHERE_LAT", max(8, int(15 * _DETAIL_SCALE)))
SPHERE_LON = _read_env_int("WARBITS_SPHERE_LON", max(16, int(30 * _DETAIL_SCALE)))
SCATTER_DEPTHSHADE = _read_env_bool("WARBITS_DEPTHSHADE", False)
PROFILE_ENABLED = _read_env_bool("WARBITS_PROFILE", False)
PROFILE_FPS_HUD = _read_env_bool("WARBITS_FPS_HUD", False)
PROFILE_FILE = _read_env_str("WARBITS_PROFILE_FILE", "")
PROFILE_SAMPLE_EVERY = _read_env_int("WARBITS_PROFILE_SAMPLE_EVERY", 1)
PROFILE_DEEP = _read_env_bool("WARBITS_PROFILE_DEEP", False)
PROFILE_MEMORY = _read_env_bool("WARBITS_PROFILE_MEMORY", PROFILE_DEEP)
PROFILE_GC = _read_env_bool("WARBITS_PROFILE_GC", PROFILE_DEEP)
PROFILE_GC_TIME = _read_env_bool("WARBITS_PROFILE_GC_TIME", PROFILE_DEEP)
PROFILE_ARTISTS = _read_env_bool("WARBITS_PROFILE_ARTISTS", PROFILE_DEEP)
PROFILE_ARTISTS_EVERY = _read_env_int("WARBITS_PROFILE_ARTISTS_EVERY", 30)
PROFILE_EVENTS = _read_env_bool("WARBITS_PROFILE_EVENTS", False)
PROFILE_AUTOFILE = _read_env_bool("WARBITS_PROFILE_AUTOFILE", True)
SCENARIO_SEED = _read_env_int_optional("WARBITS_SCENARIO_SEED")

# simulation timing (fixed-step controls)
_TARGET_FPS = _read_env_float("WARBITS_TARGET_FPS", 0.0)

_frame_interval_ms: int
if _TARGET_FPS > 0.0:
    _frame_interval_ms = max(1, int(round(1000.0 / _TARGET_FPS)))
else:
    _frame_interval_ms = _read_env_int("WARBITS_FRAME_INTERVAL_MS", 30)

FRAME_INTERVAL_MS: int = _frame_interval_ms
TARGET_FPS: float = 1000.0 / FRAME_INTERVAL_MS
SIM_REALTIME = _read_env_bool("WARBITS_SIM_REALTIME", False)
SIM_DT_MS = _read_env_float("WARBITS_SIM_DT_MS", float(FRAME_INTERVAL_MS))
SIM_MAX_STEPS = _read_env_int("WARBITS_SIM_MAX_STEPS", 1)
CELEBRATION_SECONDS = _read_env_float_nonneg("WARBITS_CELEBRATION_SECONDS", 3.0)

# adaptive render scaling (optional)
_ADAPT_RENDER_DEFAULT = AUTO_MAX_PERF and not FULLSCREEN
ADAPT_RENDER = _read_env_bool("WARBITS_ADAPT_RENDER", _ADAPT_RENDER_DEFAULT)
ADAPT_TARGET_MS = _read_env_float("WARBITS_ADAPT_TARGET_MS", float(FRAME_INTERVAL_MS))
ADAPT_WINDOW = _read_env_int("WARBITS_ADAPT_WINDOW", 30)
ADAPT_STEP = _read_env_float("WARBITS_ADAPT_STEP", 0.05)
ADAPT_MIN_SCALE = _read_env_float("WARBITS_ADAPT_MIN_SCALE", 0.60)
ADAPT_MAX_SCALE = _read_env_float("WARBITS_ADAPT_MAX_SCALE", 1.00)
ADAPT_COOLDOWN = _read_env_float("WARBITS_ADAPT_COOLDOWN", 0.75)
ADAPT_UPSCALE = _read_env_bool("WARBITS_ADAPT_UPSCALE", False)
ADAPT_FULLSCREEN = _read_env_bool("WARBITS_ADAPT_FULLSCREEN", False)
ADAPT_LOD = _read_env_bool("WARBITS_ADAPT_LOD", True)

# camera tuning
CAMERA_MODE = _read_env_str("WARBITS_CAMERA_MODE", "follow").lower()
CAMERA_LOOKAHEAD = _read_env_float_nonneg("WARBITS_CAMERA_LOOKAHEAD", 1500.0)
CAMERA_HEIGHT = _read_env_float_nonneg("WARBITS_CAMERA_HEIGHT", 300.0)
CAMERA_ELEV = _read_env_float_signed("WARBITS_CAMERA_ELEV", 30.0)
CAMERA_AZIM_OFFSET = _read_env_float_signed("WARBITS_CAMERA_AZIM_OFFSET", 180.0)
CAMERA_HEADING_SMOOTH = _read_env_float_nonneg("WARBITS_CAMERA_HEADING_SMOOTH", 0.18)
CAMERA_LOCK_CENTER = _read_env_bool("WARBITS_CAMERA_LOCK_CENTER", True)
_CAMERA_UPDATE_STRIDE_RAW = os.environ.get("WARBITS_CAMERA_UPDATE_STRIDE")
_camera_update_stride = _read_env_int("WARBITS_CAMERA_UPDATE_STRIDE", 1)
if PERF_MODE and _CAMERA_UPDATE_STRIDE_RAW is None:
    _camera_update_stride = max(2, _camera_update_stride)
CAMERA_UPDATE_STRIDE = _camera_update_stride

# physics defaults (tunable for speed vs accuracy)
BULLET_DT = _read_env_float("WARBITS_BULLET_DT", 0.02)
BULLET_MAX_TIME = _read_env_float("WARBITS_BULLET_MAX_TIME", 10.0)
BULLET_MUZZLE_SPEED = _read_env_float("WARBITS_BULLET_MUZZLE_SPEED", 20_000.0)
BULLET_SPREAD_DEG = _read_env_float("WARBITS_BULLET_SPREAD_DEG", 0.0)
BULLET_BURST = max(1, _read_env_int("WARBITS_BULLET_BURST", 1))
BULLET_DRAG = _read_env_float_nonneg("WARBITS_BULLET_DRAG", 0.0)
ROCKET_DT = _read_env_float("WARBITS_ROCKET_DT", 0.05)
ROCKET_MAX_TIME = _read_env_float("WARBITS_ROCKET_MAX_TIME", 12.0)
ROCKET_DRAG = _read_env_float_nonneg("WARBITS_ROCKET_DRAG", 0.0)
ROCKET_MASS_INITIAL = _read_env_float("WARBITS_ROCKET_MASS_INITIAL", 1.0)
ROCKET_MASS_DRY = _read_env_float("WARBITS_ROCKET_MASS_DRY", 1.0)
ROCKET_MASS_FLOW = _read_env_float("WARBITS_ROCKET_MASS_FLOW", 0.0)
BOMB_DT = _read_env_float("WARBITS_BOMB_DT", 0.5)
BOMB_MAX_TIME = _read_env_float("WARBITS_BOMB_MAX_TIME", 30.0)
BOMB_DRAG = _read_env_float_nonneg("WARBITS_BOMB_DRAG", 1.0e-3)
WIND_X = _read_env_float_signed("WARBITS_WIND_X", 0.0)
WIND_Y = _read_env_float_signed("WARBITS_WIND_Y", 0.0)
WIND_Z = _read_env_float_signed("WARBITS_WIND_Z", 0.0)
PARACHUTE_PHYSICS = _read_env_bool("WARBITS_PARACHUTE_PHYSICS", False)
PARACHUTE_GRAVITY = _read_env_float("WARBITS_PARACHUTE_GRAVITY", 9.81)
PARACHUTE_DRAG_CLOSED = _read_env_float_nonneg("WARBITS_PARACHUTE_DRAG_CLOSED", 0.02)
PARACHUTE_DRAG_OPEN = _read_env_float_nonneg("WARBITS_PARACHUTE_DRAG_OPEN", 0.12)
STRICT_PHYSICS = _read_env_bool("WARBITS_STRICT_PHYSICS", False)
PROJECTILE_AUTO_RESIZE = _read_env_bool("WARBITS_PROJECTILE_AUTO_RESIZE", True)

# ───────────────────────── figure helpers ──────────────────────────────────
def create_figure(
    *,
    figsize: Tuple[float, float] | None = None,
    dpi: int | None = None,
) -> Figure:
    """Return a bare Matplotlib `Figure` with project defaults."""
    import matplotlib.pyplot as plt

    if figsize is None:
        figsize = FIGSIZE_INCHES
    if dpi is None:
        dpi = DEFAULT_FIG_DPI
    return plt.figure(figsize=figsize, dpi=dpi)


def create_scene_canvas() -> Tuple[Figure, Axes3D]:
    """
    Build *(fig, ax)* for the main 3-D scene with styling, limits and
    fullscreen behaviour already applied.
    """
    from .style import apply_style, configure_3d_axes, make_fullscreen
    import matplotlib.pyplot as plt

    _refresh_screen()
    apply_style()
    fig = create_figure()
    ax: Axes3D = fig.add_subplot(111, projection="3d")  # type: ignore[assignment]

    configure_3d_axes(
        ax,
        xlim=(SCENE_XMIN, SCENE_XMAX),
        ylim=(SCENE_YMIN, SCENE_YMAX),
        zlim=(TERRAIN_ZMIN, TERRAIN_ZMAX),
        elev=CAMERA_ELEV,
    )
    if FULLSCREEN:
        make_fullscreen(fig)
    if FULLSCREEN:
        try:
            fig.subplots_adjust(left=0, right=1, bottom=0, top=1)
        except Exception:
            pass
    else:
        plt.tight_layout()
    return fig, ax


def make_fullscreen(fig: Figure) -> None:
    from .style import make_fullscreen as _make_fullscreen

    _make_fullscreen(fig)


# ─────────────────────────── identifiers ───────────────────────────────────
PROJECT_NAME         = "War Bits"
VERSION              = "0.1.3"
CURRENT_VEHICLE_TYPE = "AIRCRAFT"
SELECTED_VEHICLE     = "Default_Aircraft"

__all__ = [
    # canvas helpers
    "create_figure",
    "create_scene_canvas",
    "make_fullscreen",
    # screen / dpi constants
    "SCREEN_WIDTH_PX",
    "SCREEN_HEIGHT_PX",
    "RAM_GB",
    "PERF_MODE",
    "DEFAULT_FIG_DPI",
    "CANVAS_MAX_PIXELS",
    "CANVAS_SCALE",
    "FULLSCREEN",
    "FIGSIZE_INCHES",
    # quality / performance
    "AUTO_MAX_PERF",
    "TERRAIN_STEP",
    "TERRAIN_RCOUNT",
    "TERRAIN_CCOUNT",
    "TERRAIN_SHADE",
    "TERRAIN_ANTIALIASED",
    "TERRAIN_ALPHA",
    "TERRAIN_XMIN",
    "TERRAIN_XMAX",
    "TERRAIN_YMIN",
    "TERRAIN_YMAX",
    "TERRAIN_ZMIN",
    "TERRAIN_ZMAX",
    "TERRAIN_FIT_SCREEN",
    "TERRAIN_FORCE_SQUARE",
    "TERRAIN_SIZE",
    "TERRAIN_PROFILE",
    "TERRAIN_LOCK_LOD",
    "SCENE_XMIN",
    "SCENE_XMAX",
    "SCENE_YMIN",
    "SCENE_YMAX",
    "SCENE_FORCE_SQUARE",
    "SCENE_SIZE",
    "FLIGHT_TERRAIN_CLEARANCE",
    "BOGIE_SCRIPTED_HIT",
    "AIM_ASSIST",
    "VISUAL_SCALE",
    "MARKER_SCALE",
    "SPHERE_LAT",
    "SPHERE_LON",
    "SCATTER_DEPTHSHADE",
    "PROFILE_ENABLED",
    "PROFILE_FPS_HUD",
    "PROFILE_FILE",
    "PROFILE_SAMPLE_EVERY",
    "PROFILE_DEEP",
    "PROFILE_MEMORY",
    "PROFILE_GC",
    "PROFILE_GC_TIME",
    "PROFILE_ARTISTS",
    "PROFILE_ARTISTS_EVERY",
    "PROFILE_EVENTS",
    "PROFILE_AUTOFILE",
    "SCENARIO_SEED",
    "ADAPT_RENDER",
    "ADAPT_TARGET_MS",
    "ADAPT_WINDOW",
    "ADAPT_STEP",
    "ADAPT_MIN_SCALE",
    "ADAPT_MAX_SCALE",
    "ADAPT_COOLDOWN",
    "ADAPT_UPSCALE",
    "ADAPT_FULLSCREEN",
    "ADAPT_LOD",
    "CAMERA_MODE",
    "CAMERA_LOOKAHEAD",
    "CAMERA_HEIGHT",
    "CAMERA_ELEV",
    "CAMERA_AZIM_OFFSET",
    "CAMERA_HEADING_SMOOTH",
    "CAMERA_LOCK_CENTER",
    "CAMERA_UPDATE_STRIDE",
    "FRAME_INTERVAL_MS",
    "TARGET_FPS",
    "SIM_REALTIME",
    "SIM_DT_MS",
    "SIM_MAX_STEPS",
    "CELEBRATION_SECONDS",
    # physics defaults
    "BULLET_DT",
    "BULLET_MAX_TIME",
    "BULLET_MUZZLE_SPEED",
    "BULLET_SPREAD_DEG",
    "BULLET_BURST",
    "BULLET_DRAG",
    "ROCKET_DT",
    "ROCKET_MAX_TIME",
    "ROCKET_DRAG",
    "ROCKET_MASS_INITIAL",
    "ROCKET_MASS_DRY",
    "ROCKET_MASS_FLOW",
    "BOMB_DT",
    "BOMB_MAX_TIME",
    "BOMB_DRAG",
    "WIND_X",
    "WIND_Y",
    "WIND_Z",
    "PARACHUTE_PHYSICS",
    "PARACHUTE_GRAVITY",
    "PARACHUTE_DRAG_CLOSED",
    "PARACHUTE_DRAG_OPEN",
    "STRICT_PHYSICS",
    "PROJECTILE_AUTO_RESIZE",
    # identifiers
    "PROJECT_NAME",
    "VERSION",
    "CURRENT_VEHICLE_TYPE",
    "SELECTED_VEHICLE",
]
