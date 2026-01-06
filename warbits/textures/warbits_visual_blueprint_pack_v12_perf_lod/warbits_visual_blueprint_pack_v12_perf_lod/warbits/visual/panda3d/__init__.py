"""Panda3D-specific helpers for WarBits visuals.

This subpackage is safe to import even if Panda3D is not installed.
Modules that require Panda3D should guard imports internally.
"""

from .dynres import DynamicResolutionScaler

__all__ = ["DynamicResolutionScaler"]
