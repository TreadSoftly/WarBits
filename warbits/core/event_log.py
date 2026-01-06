from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable, Mapping, TypeAlias, cast

from .events import DebugEvent, ExplosionEvent, ImpactEvent, ParachuteEvent

Event: TypeAlias = ImpactEvent | ExplosionEvent | ParachuteEvent | DebugEvent


def _event_type(event: Event) -> str:
    if isinstance(event, ImpactEvent):
        return "impact"
    if isinstance(event, ExplosionEvent):
        return "explosion"
    if isinstance(event, ParachuteEvent):
        return "parachute"
    return "debug"


def _as_mapping(value: object) -> dict[str, Any]:
    if isinstance(value, Mapping):
        mapping = cast(Mapping[object, object], value)
        result: dict[str, Any] = {}
        for key, val in mapping.items():
            result[str(key)] = val
        return result
    return {}


def _coerce_int(value: object, default: int = 0) -> int:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, (str, bytes, bytearray)):
        try:
            return int(value)
        except ValueError:
            return default
    return default


def _coerce_float(value: object, default: float = 0.0) -> float:
    if isinstance(value, bool):
        return float(value)
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, (str, bytes, bytearray)):
        try:
            return float(value)
        except ValueError:
            return default
    return default


def _coerce_str(value: object, default: str = "") -> str:
    if value is None:
        return default
    return str(value)


def event_to_dict(event: Event) -> dict[str, Any]:
    data = {"type": _event_type(event)}
    data.update(event.to_dict())
    return data


def event_from_dict(data: Mapping[str, Any]) -> Event:
    kind = data.get("type")
    if kind == "impact":
        return ImpactEvent(
            frame=_coerce_int(data.get("frame")),
            x=_coerce_float(data.get("x")),
            y=_coerce_float(data.get("y")),
            z=_coerce_float(data.get("z")),
            target=_coerce_str(data.get("target")),
            weapon=_coerce_str(data.get("weapon")),
            projectile_id=(
                _coerce_int(data.get("projectile_id"))
                if "projectile_id" in data
                else None
            ),
            metadata=_as_mapping(data.get("metadata")),
        )
    if kind == "explosion":
        style_value = data.get("style")
        return ExplosionEvent(
            frame=_coerce_int(data.get("frame")),
            x=_coerce_float(data.get("x")),
            y=_coerce_float(data.get("y")),
            z=_coerce_float(data.get("z")),
            scale=_coerce_float(data.get("scale", 1.0)),
            style=_coerce_str(style_value) if style_value is not None else None,
            metadata=_as_mapping(data.get("metadata")),
        )
    if kind == "parachute":
        return ParachuteEvent(
            frame=_coerce_int(data.get("frame")),
            x=_coerce_float(data.get("x")),
            y=_coerce_float(data.get("y")),
            z=_coerce_float(data.get("z")),
            vx=_coerce_float(data.get("vx", 0.0)),
            vy=_coerce_float(data.get("vy", 0.0)),
            vz=_coerce_float(data.get("vz", 0.0)),
            metadata=_as_mapping(data.get("metadata")),
        )
    if kind == "debug":
        return DebugEvent(
            frame=_coerce_int(data.get("frame")),
            kind=_coerce_str(data.get("kind")),
            payload=_as_mapping(data.get("payload")),
        )
    raise ValueError(f"unknown event type: {kind!r}")


def write_jsonl(path: str | Path, events: Iterable[Event]) -> None:
    path = Path(path)
    with path.open("w", encoding="utf-8") as handle:
        for event in events:
            line = json.dumps(
                event_to_dict(event),
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=True,
            )
            handle.write(line + "\n")


def read_jsonl(path: str | Path) -> list[Event]:
    path = Path(path)
    events: list[Event] = []
    if not path.exists():
        return events
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            data_obj = json.loads(line)
            if not isinstance(data_obj, dict):
                raise ValueError("event log entry must be an object")
            data_dict = cast(Mapping[object, object], data_obj)
            record = _as_mapping(data_dict)
            events.append(event_from_dict(record))
    return events


__all__ = [
    "Event",
    "event_to_dict",
    "event_from_dict",
    "write_jsonl",
    "read_jsonl",
]
