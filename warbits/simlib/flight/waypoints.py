from __future__ import annotations

import math
from typing import List, Optional, Sequence

import numpy as np

from .types import Waypoint, WaypointNavigator

Vec3 = np.ndarray


def make_circle_waypoints(
    center_m: Vec3,
    radius_m: float,
    altitude_m: float,
    *,
    count: int = 12,
    acceptance_radius_m: float = 150.0,
    clockwise: bool = False,
    desired_speed_mps: Optional[float] = None,
) -> List[Waypoint]:
    """Create a simple circular patrol/orbit route.

    This is useful for:
    - enemy bogie patrol loops
    - holding patterns
    - demo scenarios

    Returns a list[Waypoint].
    """
    if count < 3:
        raise ValueError("count must be >= 3")
    c = np.asarray(center_m, dtype=float)
    if c.shape != (3,):
        raise ValueError("center_m must be shape (3,)")
    r = float(radius_m)
    if r <= 0:
        raise ValueError("radius_m must be > 0")

    wps: List[Waypoint] = []
    for i in range(count):
        theta = (2.0 * math.pi) * (i / count)
        if clockwise:
            theta = -theta
        x = float(c[0] + r * math.cos(theta))
        y = float(c[1] + r * math.sin(theta))
        z = float(altitude_m)
        wps.append(
            Waypoint(
                np.array([x, y, z], dtype=float),
                acceptance_radius_m=acceptance_radius_m,
                desired_speed_mps=desired_speed_mps,
            )
        )
    return wps


def make_line_waypoints(
    start_m: Vec3,
    end_m: Vec3,
    *,
    count: int = 10,
    acceptance_radius_m: float = 150.0,
    desired_speed_mps: Optional[float] = None,
) -> List[Waypoint]:
    """Create evenly-spaced waypoints along a straight line."""
    if count < 2:
        raise ValueError("count must be >= 2")
    a = np.asarray(start_m, dtype=float)
    b = np.asarray(end_m, dtype=float)
    if a.shape != (3,) or b.shape != (3,):
        raise ValueError("start_m and end_m must be shape (3,)")
    wps: List[Waypoint] = []
    for i in range(count):
        t = i / (count - 1)
        p = (1.0 - t) * a + t * b
        wps.append(
            Waypoint(
                np.array([float(p[0]), float(p[1]), float(p[2])], dtype=float),
                acceptance_radius_m=acceptance_radius_m,
                desired_speed_mps=desired_speed_mps,
            )
        )
    return wps


def navigator_from_waypoints(waypoints: Sequence[Waypoint], *, loop: bool = True) -> WaypointNavigator:
    """Small helper to build a navigator."""
    return WaypointNavigator(list(waypoints), loop=loop)
