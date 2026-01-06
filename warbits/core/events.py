from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, TypeAlias

Metadata: TypeAlias = dict[str, Any]


def _metadata_factory() -> Metadata:
    return {}


def _copy_metadata(value: Mapping[str, Any]) -> Metadata:
    return {str(k): v for k, v in value.items()}


@dataclass
class ImpactEvent:
    frame: int
    x: float
    y: float
    z: float
    target: str
    weapon: str
    projectile_id: int | None = None
    metadata: Metadata = field(default_factory=_metadata_factory)

    @property
    def position(self) -> tuple[float, float, float]:
        return (self.x, self.y, self.z)

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "frame": int(self.frame),
            "x": float(self.x),
            "y": float(self.y),
            "z": float(self.z),
            "target": self.target,
            "weapon": self.weapon,
        }
        if self.projectile_id is not None:
            data["projectile_id"] = int(self.projectile_id)
        if self.metadata:
            data["metadata"] = _copy_metadata(self.metadata)
        return data

    def __getitem__(self, key: str) -> Any:
        if hasattr(self, key):
            return getattr(self, key)
        if key in self.metadata:
            return self.metadata[key]
        raise KeyError(key)

    def get(self, key: str, default: Any = None) -> Any:
        try:
            return self[key]
        except KeyError:
            return default


@dataclass
class ExplosionEvent:
    frame: int
    x: float
    y: float
    z: float
    scale: float = 1.0
    style: str | None = None
    metadata: Metadata = field(default_factory=_metadata_factory)

    @property
    def position(self) -> tuple[float, float, float]:
        return (self.x, self.y, self.z)

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "frame": int(self.frame),
            "x": float(self.x),
            "y": float(self.y),
            "z": float(self.z),
            "scale": float(self.scale),
        }
        if self.style is not None:
            data["style"] = self.style
        if self.metadata:
            data["metadata"] = _copy_metadata(self.metadata)
        return data

    def __getitem__(self, key: str) -> Any:
        if hasattr(self, key):
            return getattr(self, key)
        if key in self.metadata:
            return self.metadata[key]
        raise KeyError(key)

    def get(self, key: str, default: Any = None) -> Any:
        try:
            return self[key]
        except KeyError:
            return default


@dataclass
class ParachuteEvent:
    frame: int
    x: float
    y: float
    z: float
    vx: float = 0.0
    vy: float = 0.0
    vz: float = 0.0
    metadata: Metadata = field(default_factory=_metadata_factory)

    @property
    def position(self) -> tuple[float, float, float]:
        return (self.x, self.y, self.z)

    @property
    def initial_velocity(self) -> tuple[float, float, float]:
        return (self.vx, self.vy, self.vz)

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "frame": int(self.frame),
            "x": float(self.x),
            "y": float(self.y),
            "z": float(self.z),
            "vx": float(self.vx),
            "vy": float(self.vy),
            "vz": float(self.vz),
        }
        if self.metadata:
            data["metadata"] = _copy_metadata(self.metadata)
        return data

    def __getitem__(self, key: str) -> Any:
        if hasattr(self, key):
            return getattr(self, key)
        if key in self.metadata:
            return self.metadata[key]
        raise KeyError(key)

    def get(self, key: str, default: Any = None) -> Any:
        try:
            return self[key]
        except KeyError:
            return default


@dataclass
class DebugEvent:
    frame: int
    kind: str
    payload: Metadata = field(default_factory=_metadata_factory)

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "frame": int(self.frame),
            "kind": self.kind,
        }
        if self.payload:
            data["payload"] = _copy_metadata(self.payload)
        return data

    def __getitem__(self, key: str) -> Any:
        if hasattr(self, key):
            return getattr(self, key)
        if key in self.payload:
            return self.payload[key]
        raise KeyError(key)

    def get(self, key: str, default: Any = None) -> Any:
        try:
            return self[key]
        except KeyError:
            return default


__all__ = [
    "ImpactEvent",
    "ExplosionEvent",
    "ParachuteEvent",
    "DebugEvent",
]
