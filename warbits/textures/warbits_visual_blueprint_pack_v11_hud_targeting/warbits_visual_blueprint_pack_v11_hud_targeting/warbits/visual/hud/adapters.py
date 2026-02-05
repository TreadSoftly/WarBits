"""Adapters: WarBits sim state -> HudContext.

This module isolates integration churn. If your sim state changes, update this file.

We keep imports optional to avoid hard dependencies during library development.
"""

from __future__ import annotations

from typing import Any, Optional, cast

import numpy as np

from .types import CameraInfo, HudContext, TargetTrack, Vec3, WeaponInfo


def build_context_from_warbits_state(
    state: Any,
    *,
    time_s: float,
    camera_pos_m: Vec3,
    camera_forward: Vec3,
    camera_up: Vec3,
    fov_y_deg: float,
    aspect: float,
    selected_track_id: Optional[str] = None,
    weapon: Optional[WeaponInfo] = None,
) -> HudContext:
    """Best-effort adapter.

    Expected state shape (approx):
    - state.flight.plane_pos: np.ndarray(3)
    - state.flight.plane_vel: np.ndarray(3)
    - state.enemies: iterable with .pos and .vel (optional)

    This function is intentionally defensive: missing fields degrade gracefully.
    """

    own_pos = _get_vec3(state, "flight.plane_pos", default=np.zeros(3, dtype=float))
    own_vel = _get_vec3(state, "flight.plane_vel", default=np.zeros(3, dtype=float))

    speed = float(np.linalg.norm(own_vel))
    alt = float(own_pos[2])

    heading = _heading_from_vel(own_vel)

    tracks = _extract_tracks(state)

    cam = CameraInfo(
        position_m=camera_pos_m.astype(float),
        forward=camera_forward.astype(float),
        up=camera_up.astype(float),
        fov_y_deg=float(fov_y_deg),
        aspect=float(aspect),
    )

    return HudContext(
        time_s=float(time_s),
        ownship_pos_m=own_pos,
        ownship_vel_mps=own_vel,
        ownship_heading_deg=heading,
        ownship_alt_m=alt,
        ownship_speed_mps=speed,
        camera=cam,
        tracks=tuple(tracks),
        selected_track_id=selected_track_id,
        weapon=weapon or WeaponInfo(),
        debug={},
    )


def _heading_from_vel(v: Vec3) -> float:
    if float(np.linalg.norm(v[:2])) < 1e-9:
        return 0.0
    ang = np.degrees(np.arctan2(v[1], v[0]))
    if ang < 0:
        ang += 360.0
    return float(ang)


def _extract_tracks(state: Any) -> list[TargetTrack]:
    tracks: list[TargetTrack] = []

    # Enemy ground system
    for key in ("enemy_ground", "ground", "ground_units"):
        units = getattr(state, key, None)
        if units is None:
            continue
        # Attempt common patterns
        for i, u in enumerate(_iterable_or_empty(units)):
            pos = _maybe_vec3(getattr(u, "pos", None)) or _maybe_vec3(getattr(u, "position", None))
            if pos is None:
                continue
            vel = _maybe_vec3(getattr(u, "vel", None)) or np.zeros(3)
            tracks.append(
                TargetTrack(track_id=f"G{i}", position_m=pos, velocity_mps=vel, classification="ground", hostile=True)
            )

    # Enemy bogies system
    for key in ("enemy_bogies", "bogies", "air_units"):
        units = getattr(state, key, None)
        if units is None:
            continue
        for i, u in enumerate(_iterable_or_empty(units)):
            pos = _maybe_vec3(getattr(u, "pos", None)) or _maybe_vec3(getattr(u, "position", None))
            if pos is None:
                continue
            vel = _maybe_vec3(getattr(u, "vel", None)) or np.zeros(3)
            tracks.append(
                TargetTrack(track_id=f"A{i}", position_m=pos, velocity_mps=vel, classification="air", hostile=True)
            )

    # Fallback: if state has enemies list of dicts
    enemies = getattr(state, "enemies", None)
    if enemies is not None:
        for i, e in enumerate(_iterable_or_empty(enemies)):
            if isinstance(e, dict):
                e_dict = cast(dict[str, Any], e)
                pos = _maybe_vec3(e_dict.get("pos"))
                vel = _maybe_vec3(e_dict.get("vel"))
            else:
                pos = _maybe_vec3(getattr(e, "pos", None))
                vel = _maybe_vec3(getattr(e, "vel", None))
            if pos is None:
                continue
            vel = vel or np.zeros(3, dtype=float)
            tracks.append(
                TargetTrack(track_id=f"T{i}", position_m=pos, velocity_mps=vel, classification="unknown", hostile=True)
            )

    return tracks


def _get_vec3(obj: Any, dotted: str, default: Vec3) -> Vec3:
    cur = obj
    for part in dotted.split("."):
        cur = getattr(cur, part, None)
        if cur is None:
            return default.astype(float)
    v = _maybe_vec3(cur)
    return v if v is not None else default.astype(float)


def _maybe_vec3(v: Any) -> Optional[Vec3]:
    if v is None:
        return None
    arr = np.asarray(v, dtype=float).reshape(-1)
    if arr.size < 3:
        return None
    return arr[:3].astype(float)


def _iterable_or_empty(x: Any) -> list[Any]:
    try:
        return list(x)
    except Exception:
        return []
