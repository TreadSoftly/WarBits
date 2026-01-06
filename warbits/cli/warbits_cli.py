from __future__ import annotations

import argparse
import os
import sys
from importlib import import_module
from types import ModuleType
from typing import NoReturn

# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #
def _fatal(msg: str) -> NoReturn:
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(2)


def _dump_config() -> None:
    try:
        from warbits.config import settings as _cfg
    except Exception:
        _fatal("Could not import warbits.config.settings")

    items: list[tuple[str, object]] = [
        ("WIND_X", _cfg.WIND_X),
        ("WIND_Y", _cfg.WIND_Y),
        ("WIND_Z", _cfg.WIND_Z),
        ("BULLET_DRAG", _cfg.BULLET_DRAG),
        ("ROCKET_DRAG", _cfg.ROCKET_DRAG),
        ("BOMB_DRAG", _cfg.BOMB_DRAG),
        ("PARACHUTE_DRAG_CLOSED", _cfg.PARACHUTE_DRAG_CLOSED),
        ("PARACHUTE_DRAG_OPEN", _cfg.PARACHUTE_DRAG_OPEN),
        ("TERRAIN_FIT_SCREEN", _cfg.TERRAIN_FIT_SCREEN),
        ("TERRAIN_FORCE_SQUARE", _cfg.TERRAIN_FORCE_SQUARE),
        ("TERRAIN_XMIN", _cfg.TERRAIN_XMIN),
        ("TERRAIN_XMAX", _cfg.TERRAIN_XMAX),
        ("TERRAIN_YMIN", _cfg.TERRAIN_YMIN),
        ("TERRAIN_YMAX", _cfg.TERRAIN_YMAX),
    ]

    for key, value in items:
        print(f"{key}={value}")


def _launch_sim(*, max_perf: bool = False) -> None:
    auto_perf = False
    try:
        from warbits.config import settings as _cfg

        auto_perf = _cfg.AUTO_MAX_PERF
    except Exception:
        auto_perf = False

    if max_perf or auto_perf:
        try:
            from warbits.utils import concurrency as _conc

            _conc.use_all_cores()
        except Exception:
            pass  # silent fail - no logging

    try:
        animation: ModuleType = import_module("warbits.scene.animation")
    except Exception:
        _fatal("Could not import warbits.scene.animation")

    runner = getattr(animation, "run_animation", None)
    if runner is None:
        _fatal("'run_animation' not found in warbits.scene.animation")

    try:
        import matplotlib
    except Exception:
        _fatal("Matplotlib is not available")

    if (
        matplotlib.get_backend().lower() in {"agg", "svg"}
        and os.environ.get("DISPLAY", "") == ""
    ):
        _fatal("Matplotlib is running in a non-interactive backend")

    runner()

# --------------------------------------------------------------------------- #
# argparse plumbing
# --------------------------------------------------------------------------- #
def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="warbits",
        description="War Bits 3-D flight & gunnery simulator",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    loop_grp = p.add_mutually_exclusive_group()
    loop_grp.add_argument(
        "--loop",
        dest="loop",
        action="store_true",
        default=None,
        help="repeat animation (default)",
    )
    loop_grp.add_argument(
        "--no-loop",
        dest="loop",
        action="store_false",
        help="disable animation repeat",
    )

    p.add_argument(
        "--max-perf",
        action="store_true",
        help="enable CPU warm-up if available",
    )

    sub = p.add_subparsers(dest="command", required=False)
    sub.add_parser("run", help="launch the full simulation window")
    sub.add_parser("config", help="print resolved config and exit")

    return p


def build_parser() -> argparse.ArgumentParser:
    return _build_parser()


def main(argv: list[str] | None = None) -> None:
    if argv is None:
        argv = sys.argv[1:]

    parser = _build_parser()
    ns = parser.parse_args(argv)

    if ns.loop is not None:
        os.environ["WARBITS_LOOP"] = "1" if ns.loop else "0"

    cmd = ns.command or "run"

    if cmd == "run":
        _launch_sim(max_perf=ns.max_perf)
    elif cmd == "config":
        _dump_config()
    else:  # pragma: no cover
        parser.error(f"unknown command: {cmd!r}")


__all__ = ["build_parser", "main"]
