"""Build a HUD drawlist from a HudContext.

This module is the "brains" of the HUD. It outputs renderer-agnostic primitives.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Sequence, Tuple

import numpy as np

from .layout import DEFAULT_LAYOUT, HudLayout
from .projector import ScreenProjector
from .targeting import lead_solution_simple
from .types import HudBox, HudCircle, HudContext, HudDrawList, HudLine, HudPrimitive, HudText, HudTheme, TargetTrack


@dataclass
class HudBuilder:
    theme: HudTheme = HudTheme()
    layout: HudLayout = DEFAULT_LAYOUT

    def build(self, ctx: HudContext, projector: ScreenProjector) -> HudDrawList:
        prims: list[HudPrimitive] = []

        # --- Basic telemetry (War Thunder-ish) ---
        prims.append(
            HudText(
                pos=self.layout.speed_pos,
                text=f"SPD {ctx.ownship_speed_mps:6.1f} m/s",
                color_key=self.theme.ui,
                size_px=12,
            )
        )
        prims.append(
            HudText(
                pos=self.layout.alt_pos,
                text=f"ALT {ctx.ownship_alt_m:7.0f} m",
                color_key=self.theme.ui,
                size_px=12,
            )
        )
        prims.append(
            HudText(
                pos=self.layout.heading_pos,
                text=f"HDG {ctx.ownship_heading_deg:06.1f}°",
                color_key=self.theme.ui,
                size_px=12,
                align="center",
                valign="top",
            )
        )

        # --- Crosshair ---
        prims.extend(self._crosshair())

        # --- Horizon (simple pitch indicator) ---
        prims.extend(self._horizon(ctx))

        # --- Target symbology ---
        tgt = _select_track(ctx.tracks, ctx.selected_track_id)
        if tgt is not None:
            prims.extend(self._target_box(ctx, projector, tgt))
            prims.extend(self._lead_pipper(ctx, projector, tgt))

        # Optional debug text
        y = 0.75
        for k, v in sorted(ctx.debug.items()):
            prims.append(HudText(pos=(-0.98, y), text=f"{k}: {v}", size_px=10, color_key=self.theme.ui))
            y -= 0.06

        # Pixel snapping (optional)
        if self.theme.pixel_snap and self.theme.pixel_snap > 0:
            prims = [_pixel_snap_primitive(p, self.theme.pixel_snap) for p in prims]

        return HudDrawList(primitives=tuple(prims))

    def _crosshair(self) -> list[HudPrimitive]:
        c = 0.0
        half = self.layout.crosshair_half
        gap = self.layout.crosshair_gap
        w = self.theme.line_width_px

        return [
            HudLine(a=(c - half, 0.0), b=(c - gap, 0.0), width_px=w),
            HudLine(a=(c + gap, 0.0), b=(c + half, 0.0), width_px=w),
            HudLine(a=(0.0, c - half), b=(0.0, c - gap), width_px=w),
            HudLine(a=(0.0, c + gap), b=(0.0, c + half), width_px=w),
        ]

    def _horizon(self, ctx: HudContext) -> list[HudPrimitive]:
        # Very light-weight pitch cue based on camera forward vector.
        fwd = ctx.camera.forward
        fwd = fwd / (np.linalg.norm(fwd) + 1e-9)
        pitch = float(np.arcsin(np.clip(fwd[2], -1.0, 1.0)))  # radians

        # Map pitch to a screen y offset. This isn't exact; it's a cheap cue.
        fov_y = np.deg2rad(max(1e-3, ctx.camera.fov_y_deg))
        y = float(-pitch / (0.5 * fov_y))
        y = float(np.clip(y, -0.8, 0.8))

        hw = self.layout.horizon_half_width
        return [
            HudLine(
                a=(-hw, y),
                b=(hw, y),
                width_px=self.layout.horizon_thickness_px,
                alpha=0.55,
            )
        ]

    def _target_box(self, ctx: HudContext, projector: ScreenProjector, tgt: TargetTrack) -> list[HudPrimitive]:
        ndc = projector.project_ndc(tgt.position_m)
        if ndc is None:
            return []

        dx, dy = self.layout.target_label_offset
        dist = float(np.linalg.norm(tgt.position_m - ctx.ownship_pos_m))

        color = self.theme.hostile if tgt.hostile else self.theme.friendly
        he = (self.layout.target_box_half, self.layout.target_box_half)

        return [
            HudBox(center=ndc, half_extents=he, color_key=color, width_px=1.2, alpha=0.9),
            HudText(
                pos=(ndc[0] + dx, ndc[1] + dy),
                text=f"{tgt.track_id}  {dist:,.0f}m",
                color_key=color,
                size_px=10,
            ),
        ]

    def _lead_pipper(self, ctx: HudContext, projector: ScreenProjector, tgt: TargetTrack) -> list[HudPrimitive]:
        w = ctx.weapon
        if w.weapon_family not in ("gun", "rocket", "missile"):
            return []
        if w.muzzle_speed_mps <= 1e-3:
            return []

        sol = lead_solution_simple(
            shooter_pos_m=ctx.ownship_pos_m,
            shooter_vel_mps=ctx.ownship_vel_mps,
            target_pos_m=tgt.position_m,
            target_vel_mps=tgt.velocity_mps,
            projectile_speed_mps=w.muzzle_speed_mps,
            gravity_mps2=w.gravity_mps2,
        )
        if sol is None:
            return []

        ndc = projector.project_ndc(sol.aim_point_m)
        if ndc is None:
            return []

        # Lead circle + tiny tick
        color = self.theme.warning if tgt.hostile else self.theme.ui
        return [
            HudCircle(center=ndc, radius=self.layout.lead_radius, color_key=color, width_px=1.2, alpha=0.95),
            HudLine(
                a=(ndc[0] - 0.015, ndc[1]),
                b=(ndc[0] + 0.015, ndc[1]),
                color_key=color,
                width_px=1.0,
                alpha=0.85,
            ),
        ]


def _select_track(tracks: Sequence[TargetTrack], selected_id: Optional[str]) -> Optional[TargetTrack]:
    if not tracks:
        return None
    if selected_id:
        for t in tracks:
            if t.track_id == selected_id and t.alive:
                return t
    # fallback: nearest hostile alive
    alive = [t for t in tracks if t.alive]
    return alive[0] if alive else None


def _snap_ndc(p: Tuple[float, float], pixel_snap: int) -> Tuple[float, float]:
    # pixel_snap is "pixels per half-axis" (so 100 => 200px across)
    s = float(pixel_snap)
    x = round(p[0] * s) / s
    y = round(p[1] * s) / s
    return (float(x), float(y))


def _pixel_snap_primitive(p: HudPrimitive, pixel_snap: int) -> HudPrimitive:
    from .types import HudBox, HudCircle, HudLine, HudText

    if isinstance(p, HudLine):
        return HudLine(
            a=_snap_ndc(p.a, pixel_snap),
            b=_snap_ndc(p.b, pixel_snap),
            color_key=p.color_key,
            width_px=p.width_px,
            dashed=p.dashed,
            alpha=p.alpha,
        )
    if isinstance(p, HudCircle):
        return HudCircle(
            center=_snap_ndc(p.center, pixel_snap),
            radius=p.radius,
            color_key=p.color_key,
            width_px=p.width_px,
            dashed=p.dashed,
            alpha=p.alpha,
        )
    if isinstance(p, HudBox):
        return HudBox(
            center=_snap_ndc(p.center, pixel_snap),
            half_extents=p.half_extents,
            color_key=p.color_key,
            width_px=p.width_px,
            alpha=p.alpha,
        )
    return HudText(
        pos=_snap_ndc(p.pos, pixel_snap),
        text=p.text,
        color_key=p.color_key,
        size_px=p.size_px,
        align=p.align,
        valign=p.valign,
        alpha=p.alpha,
    )
