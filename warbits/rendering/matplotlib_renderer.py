from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, TYPE_CHECKING

import numpy as np
from numpy.typing import NDArray

from ..config import settings as _cfg
from ..logic import (
    register_aircraft_axes as _register_aircraft_axes,
    reset_aircraft as _reset_aircraft,
    step_aircraft,
)
from ..logic.state import RuntimeState
from ..physics.explosions import register_axes as _register_explosions, update_explosion
from ..physics.parachute import register_axes as _register_parachutes, update_parachute
from ..physics.terrain import draw_terrain as _draw_terrain
from .base import RendererAdapter

if TYPE_CHECKING:
    from matplotlib.figure import Figure
    from mpl_toolkits.mplot3d import Axes3D  # type: ignore[import-not-found]


@dataclass
class TerrainContext:
    step: int
    rcount: int
    ccount: int
    profile: str | None
    seed: int | None


@dataclass
class MatplotlibRenderer(RendererAdapter):
    fig: "Figure | None" = None
    ax: "Axes3D | None" = None
    terrain_context: TerrainContext | None = None
    terrain_surface: Any | None = None
    bullet_scatter: Any | None = None
    rocket_scatter: Any | None = None
    bomb_scatter: Any | None = None
    _rocket_colors: tuple[str, ...] = field(
        default_factory=lambda: ("magenta", "cyan", "blue", "pink")
    )
    _bomb_colors: tuple[str, ...] = field(
        default_factory=lambda: ("white", "red", "yellow", "orange")
    )

    def init_scene(self, sim_state: RuntimeState) -> None:
        if self.fig is None or self.ax is None:
            self.fig, self.ax = _cfg.create_scene_canvas()
            _register_aircraft_axes(self.ax)
            _register_explosions(self.ax)
            _register_parachutes(self.ax)

    def begin_frame(self, frame_idx: int, sim_state: RuntimeState) -> None:
        return None

    def set_terrain_context(
        self,
        *,
        step: int,
        rcount: int,
        ccount: int,
        profile: str | None,
        seed: int | None,
    ) -> None:
        self.terrain_context = TerrainContext(
            step=step,
            rcount=rcount,
            ccount=ccount,
            profile=profile,
            seed=seed,
        )

    def draw_terrain(self, sim_state: RuntimeState) -> None:
        if self.ax is None:
            return
        ctx = self.terrain_context
        if ctx is None:
            ctx = TerrainContext(
                step=_cfg.TERRAIN_STEP,
                rcount=_cfg.TERRAIN_RCOUNT,
                ccount=_cfg.TERRAIN_CCOUNT,
                profile=_cfg.TERRAIN_PROFILE,
                seed=_cfg.SCENARIO_SEED,
            )
            self.terrain_context = ctx
        if self.terrain_surface is not None:
            try:
                self.terrain_surface.remove()
            except Exception:
                pass
            self.terrain_surface = None
        _, _, _, self.terrain_surface = _draw_terrain(
            self.ax,
            step=ctx.step,
            rcount=ctx.rcount,
            ccount=ctx.ccount,
            profile=ctx.profile,
            seed=ctx.seed,
            return_surface=True,
        )

    def draw_aircraft(self, sim_state: RuntimeState) -> None:
        if self.ax is None:
            return
        step_aircraft(sim_state.flight.plane_pos, sim_state.flight.plane_vel)

    def _update_scatter(
        self,
        scatter: Any | None,
        xs: NDArray[np.float32],
        ys: NDArray[np.float32],
        zs: NDArray[np.float32],
    ) -> Any | None:
        if xs.size == 0:
            if scatter is not None:
                try:
                    scatter.set_visible(False)
                except Exception:
                    pass
            return scatter
        if scatter is None:
            return None
        try:
            scatter._offsets3d = (xs, ys, zs)  # type: ignore[attr-defined]
            scatter.set_visible(True)
        except Exception:
            pass
        return scatter

    def draw_projectiles(self, sim_state: RuntimeState) -> None:
        if self.ax is None:
            return
        ax_any: Any = self.ax

        xs, ys, zs, _rows = sim_state.active_bullets.sample_positions()
        if self.bullet_scatter is None and xs.size > 0:
            self.bullet_scatter = ax_any.scatter(
                xs,
                ys,
                zs,
                color="yellow",
                marker=".",
                s=10,
                depthshade=_cfg.SCATTER_DEPTHSHADE,
            )
        self.bullet_scatter = self._update_scatter(self.bullet_scatter, xs, ys, zs)

        xs, ys, zs, _rows = sim_state.active_rockets.sample_positions()
        if self.rocket_scatter is None and xs.size > 0:
            self.rocket_scatter = ax_any.scatter(
                xs,
                ys,
                zs,
                marker="^",
                s=40,
                color=self._rocket_colors[0],
                depthshade=_cfg.SCATTER_DEPTHSHADE,
            )
        self.rocket_scatter = self._update_scatter(self.rocket_scatter, xs, ys, zs)
        if self.rocket_scatter is not None and xs.size > 0:
            color = self._rocket_colors[(sim_state.flight.frame // 5) % len(self._rocket_colors)]
            try:
                self.rocket_scatter.set_color(color)
            except Exception:
                pass

        xs, ys, zs, _rows = sim_state.active_bombs.sample_positions()
        if self.bomb_scatter is None and xs.size > 0:
            self.bomb_scatter = ax_any.scatter(
                xs,
                ys,
                zs,
                s=50,
                color="white",
                depthshade=_cfg.SCATTER_DEPTHSHADE,
            )
        self.bomb_scatter = self._update_scatter(self.bomb_scatter, xs, ys, zs)
        if self.bomb_scatter is not None and xs.size > 0:
            blink = max(1, 10 - int(max(float(np.max(zs)), 0.0) / 100.0))
            color = self._bomb_colors[(sim_state.flight.frame // blink) % len(self._bomb_colors)]
            try:
                self.bomb_scatter.set_color(color)
            except Exception:
                pass

    def draw_entities(self, sim_state: RuntimeState) -> None:
        return None

    def draw_events(self, sim_state: RuntimeState) -> None:
        update_explosion()
        update_parachute()

    def end_frame(self, frame_idx: int, sim_state: RuntimeState) -> None:
        return None

    def shutdown(self) -> None:
        _reset_aircraft()
        if self.terrain_surface is not None:
            try:
                self.terrain_surface.remove()
            except Exception:
                pass
            self.terrain_surface = None
        for scatter in (self.bullet_scatter, self.rocket_scatter, self.bomb_scatter):
            if scatter is None:
                continue
            try:
                scatter.remove()
            except Exception:
                pass
        self.bullet_scatter = None
        self.rocket_scatter = None
        self.bomb_scatter = None
