from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FxConfig:
    """Top-level FX configuration.

    This config is **renderer-agnostic**. It only controls geometry density,
    lifetimes, and caps. Color/line styling is owned by renderer styles.

    Performance notes
    -----------------
    - Caps are hard caps. If you exceed a cap, the system reuses slots in a
      deterministic round-robin manner.
    - The defaults are conservative so you can crank them up after measuring.
    """

    # Tracers: short trails behind fast bullets/rockets.
    tracer_max_objects: int = 800
    tracer_history: int = 4  # points per object; segments ~ history-1
    tracer_fade_power: float = 1.8
    max_tracer_segments: int = 2400

    # Contrails/smoke: longer aircraft trails.
    contrail_max_objects: int = 64
    contrail_history: int = 18
    contrail_fade_power: float = 1.4
    max_contrail_segments: int = 1200
    max_smoke_segments: int = 1200

    # Explosions: wireframe spheres.
    max_explosions: int = 96
    explosion_lifetime_frames: int = 24
    explosion_max_radius_m: float = 18.0

    # Impacts: small bursts at the hit point.
    max_impacts: int = 192
    impact_lifetime_frames: int = 10
    impact_radius_m: float = 6.0

    # Geometry density knobs.
    explosion_lat_steps: int = 6
    explosion_lon_steps: int = 12

    impact_rays: int = 10  # number of burst rays

    # Optional global LOD control: scale down emitted segments.
    # 1.0 = full density; 0.5 = roughly half of segments (implementation-dependent)
    global_lod: float = 1.0

    # Debug behavior.
    strict: bool = False
