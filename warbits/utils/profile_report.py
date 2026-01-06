from __future__ import annotations

import json
import sys
from collections import defaultdict
from collections.abc import Mapping
from pathlib import Path
from typing import Any, TypeGuard, cast


JsonDict = dict[str, object]


def _is_number(value: object) -> TypeGuard[int | float]:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _as_float(value: object, default: float = 0.0) -> float:
    if isinstance(value, bool):
        return default
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(cast(Any, value))
    except (TypeError, ValueError):
        return default


def _as_int(value: object, default: int = -1) -> int:
    if isinstance(value, bool):
        return default
    if isinstance(value, int):
        return int(value)
    if isinstance(value, float):
        return int(value)
    try:
        return int(cast(Any, value))
    except (TypeError, ValueError):
        return default


def _p90(values: list[float]) -> float:
    if not values:
        return 0.0
    values = sorted(values)
    idx = int(0.9 * (len(values) - 1))
    return values[idx]


def _parse_args(argv: list[str]) -> tuple[Path, int, bool]:
    path = Path("profiling/run.jsonl")
    top = 5
    show_all = False
    for arg in argv:
        if arg == "--all":
            show_all = True
            continue
        if arg.startswith("--top="):
            try:
                top = max(1, int(arg.split("=", 1)[1]))
            except ValueError:
                pass
            continue
        path = Path(arg)
    return path, top, show_all


def _summarize_metric(values: list[float]) -> tuple[float, float, float]:
    if not values:
        return 0.0, 0.0, 0.0
    avg = sum(values) / len(values)
    return avg, _p90(values), max(values)


def main() -> int:
    path, top_n, show_all = _parse_args(sys.argv[1:])
    if not path.is_file():
        print(f"[profile] Missing file: {path}")
        return 2

    meta: JsonDict | None = None
    summary: JsonDict | None = None
    frames: list[JsonDict] = []
    events: list[JsonDict] = []
    series: dict[str, list[float]] = defaultdict(list)

    with path.open("r", encoding="utf-8") as handle:
        for raw in handle:
            raw = raw.strip()
            if not raw:
                continue
            try:
                item = json.loads(raw)
            except json.JSONDecodeError:
                continue
            if not isinstance(item, dict):
                continue
            item_dict = cast(JsonDict, item)
            if "meta" in item_dict:
                meta_value = item_dict.get("meta")
                if isinstance(meta_value, dict):
                    meta = cast(JsonDict, meta_value)
                continue
            if "summary" in item_dict:
                summary_value = item_dict.get("summary")
                if isinstance(summary_value, dict):
                    summary = cast(JsonDict, summary_value)
                continue
            if "event" in item_dict:
                events.append(item_dict)
                continue
            if "frame" in item_dict:
                frames.append(item_dict)
                for key, value in item_dict.items():
                    if _is_number(value) and key != "frame":
                        series[key].append(float(value))

    print(f"[profile] File: {path}")
    if meta:
        backend = meta.get("backend", "unknown")
        mpl = meta.get("matplotlib", "unknown")
        fig_dpi = meta.get("fig_dpi", "unknown")
        canvas_px = meta.get("canvas_px", "unknown")
        dpr = meta.get("device_pixel_ratio", "unknown")
        pixel_total = meta.get("pixel_total", "unknown")
        settings = meta.get("settings")
        scale_text = "unknown"
        fullscreen_text = "unknown"
        if isinstance(settings, Mapping):
            settings_map = cast(Mapping[str, object], settings)
            if "canvas_scale" in settings_map:
                scale_text = f"{_as_float(settings_map.get('canvas_scale', 0.0)):.3f}"
            if "fullscreen" in settings_map:
                fullscreen_text = str(settings_map.get("fullscreen"))
        if _is_number(pixel_total):
            pixel_total = _as_int(pixel_total)
        print(
            "[profile] Backend="
            f"{backend} Matplotlib={mpl} DPI={fig_dpi} CanvasPx={canvas_px} "
            f"PxTotal={pixel_total} DPR={dpr} Scale={scale_text} Fullscreen={fullscreen_text}"
        )
    print(f"[profile] Frames: {len(frames)} Events: {len(events)}")

    def _top_by(key: str) -> list[dict[str, object]]:
        items = [f for f in frames if key in f]
        return sorted(items, key=lambda f: _as_float(f.get(key, 0.0)), reverse=True)[:top_n]

    if frames:
        for label, key in (("render", "render_ms"), ("total", "total_ms")):
            top = _top_by(key)
            if not top:
                continue
            print(f"[profile] Top {label} frames:")
            for entry in top:
                frame = _as_int(entry.get("frame", -1))
                val = _as_float(entry.get(key, 0.0))
                interval = _as_float(entry.get("interval_ms", 0.0))
                print(f"  frame={frame} {key}={val} interval_ms={interval}")

    if series:
        keys = sorted(series.keys())
        if not show_all:
            keys = [k for k in keys if k.endswith("_ms") or k.endswith("_n") or k in {"render_ms", "total_ms"}]
        print("[profile] Metrics (avg/p90/max):")
        for key in keys:
            avg, p90, mx = _summarize_metric(series[key])
            print(f"  {key}: {avg:.3f} / {p90:.3f} / {mx:.3f}")

    if summary:
        print("[profile] Summary line present in log.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
