"""WarBits shared exception types.

This module is intentionally tiny, dependency-free, and safe to import anywhere.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Optional


class WarBitsError(Exception):
    """Base class for WarBits exceptions."""


@dataclass
class ErrorContext:
    """Structured context for debugging.

    Keep this JSON-serializable so it can be emitted into event logs / manifests.
    """

    where: str
    details: Mapping[str, Any]


class PhysicsError(WarBitsError):
    """Raised when a physics solver detects an invalid state or fails."""

    def __init__(
        self,
        message: str,
        *,
        context: Optional[ErrorContext] = None,
        cause: Optional[BaseException] = None,
    ) -> None:
        super().__init__(message)
        self.context = context
        self.__cause__ = cause  # preserve original exception chain


class StrictPhysicsError(PhysicsError):
    """Raised when strict physics mode is enabled and the solver would otherwise recover."""


class DataError(WarBitsError):
    """Raised for invalid or inconsistent data (schemas, cross-links, units)."""


class DeterminismError(WarBitsError):
    """Raised when a determinism invariant is violated (e.g., non-finite state)."""


class ConfigError(WarBitsError):
    """Raised for invalid configuration."""
