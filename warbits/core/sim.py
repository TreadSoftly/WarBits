from __future__ import annotations

import hashlib
import json
import secrets
from dataclasses import dataclass
from typing import Any, Callable

import numpy as np

from ..config import settings as _cfg
from ..core.events import DebugEvent, ExplosionEvent, ImpactEvent
from ..core.services import SimClock, SimServices, TerrainQuery
from ..logic import engagement
from ..logic.flight_paths import DEFAULT_PHASES, build_flight_plan
from ..logic.mission_runtime import (
    DEFAULT_TIME_LIMIT_S,
    MissionRuntime,
    build_runtime_world,
    build_time_limit_mission,
)
from ..simlib.mission.directives import MissionDirective
from ..simlib.mission.director import MissionTickResult
from ..logic.scenario import ActionSchedule, DecisionDirector, DecisionState, ScenarioDirector
from ..logic.state import RUNTIME, RuntimeState
from ..logic.weather import WeatherDirector, WeatherState
from ..physics.terrain import sample_height
from ..simlib.rng import DeterministicRNG

StepCallback = Callable[[int], dict[str, float]]

_BOMB_EXPLOSION_SCALE = 9.0
_ROCKET_EXPLOSION_SCALE = 0.6


@dataclass
class SimSummary:
    frames: int
    impacts: int
    explosions: int
    parachutes: int
    hash: str


class Simulation:
    def __init__(
        self,
        *,
        runtime: RuntimeState | None = None,
        seed: int | None = None,
        step_callback: StepCallback | None = None,
    ) -> None:
        self.runtime = runtime or RUNTIME
        self._step_callback = step_callback
        self._frame = 0
        self._seed = seed if seed is not None else _cfg.SCENARIO_SEED
        self._root_seed = self._seed if self._seed is not None else secrets.randbits(32)
        dt_s = max(float(_cfg.SIM_DT_MS) / 1000.0, 1e-6)
        self.services = SimServices(
            rng=DeterministicRNG.from_seed(self._root_seed, context="simulation"),
            clock=SimClock(dt_s=dt_s),
            terrain=TerrainQuery(height=sample_height),
            config=_cfg,
        )
        self._flight_rng = None
        self._engagement_rng = None
        self._flight_x = np.empty(0, dtype=np.float64)
        self._flight_y = np.empty(0, dtype=np.float64)
        self._flight_z = np.empty(0, dtype=np.float64)
        self._flight_vx = np.empty(0, dtype=np.float64)
        self._flight_vy = np.empty(0, dtype=np.float64)
        self._flight_vz = np.empty(0, dtype=np.float64)
        self._slice_map: dict[str, tuple[int, int]] = {}
        self._n_frames = 0
        self._prev_pos: tuple[float, float, float] | None = None
        self._scenario: ActionSchedule | None = None
        self._decision_state: DecisionState | None = None
        self._weather: WeatherState | None = None
        self._scenario_director = ScenarioDirector(seed=self._seed)
        self._decision_director = DecisionDirector(seed=self._seed)
        self._weather_director = WeatherDirector(seed=self._seed)
        self._mission_runtime: MissionRuntime | None = MissionRuntime(
            director=build_time_limit_mission(time_limit_s=DEFAULT_TIME_LIMIT_S),
            world=build_runtime_world(
                self.runtime,
                lambda: float(self.services.clock.time_s),
            ),
        )
        self._mission_runtime.reset()
        self._mission_result: MissionTickResult | None = None
        if self._step_callback is None:
            self._init_headless()

    def _init_headless(self) -> None:
        self.services.reset_rngs()
        self._flight_rng = self.services.py_random("flight_plan")
        self._engagement_rng = self.services.numpy_rng("engagement")
        flight_x, flight_y, flight_z, slice_map = build_flight_plan(
            DEFAULT_PHASES,
            rng=self._flight_rng,
        )
        self._flight_x = flight_x
        self._flight_y = flight_y
        self._flight_z = flight_z
        self._slice_map = slice_map
        self._n_frames = int(flight_x.size)
        dt_s = max(float(_cfg.SIM_DT_MS) / 1000.0, 1e-6)
        self._flight_vx = np.empty_like(flight_x)
        self._flight_vy = np.empty_like(flight_y)
        self._flight_vz = np.empty_like(flight_z)
        if self._n_frames > 0:
            self._flight_vx[0] = 0.0
            self._flight_vy[0] = 0.0
            self._flight_vz[0] = 0.0
            self._flight_vx[1:] = np.diff(flight_x) / dt_s
            self._flight_vy[1:] = np.diff(flight_y) / dt_s
            self._flight_vz[1:] = np.diff(flight_z) / dt_s
        scenario_seed = int(self.services.substream("scenario").root_seed_u64)
        self._scenario = self._scenario_director.build(self._slice_map, seed=scenario_seed)
        self._decision_state = self._decision_director.reset(
            self._slice_map, seed=self._scenario.seed
        )
        self._weather = self._weather_director.build(seed=self._scenario.seed)
        self.runtime.environment.wind = self._weather.wind
        if self._mission_runtime is not None:
            self._mission_runtime.reset()

    def reset(self) -> None:
        self._frame = 0
        self._prev_pos = None
        self.runtime.active_bullets.clear()
        self.runtime.active_rockets.clear()
        self.runtime.active_bombs.clear()
        self.runtime.impacts.clear()
        self.runtime.explosions.clear()
        self.runtime.parachutes.clear()
        self.runtime.debug_events.clear()
        if self._mission_runtime is not None:
            self._mission_runtime.reset()
            self._mission_result = None
        if self._step_callback is None:
            self._init_headless()

    def step(self, frame_idx: int | None = None) -> dict[str, float]:
        if frame_idx is None:
            frame_idx = self._frame
            self._frame += 1
        if self._step_callback is not None:
            return self._step_callback(frame_idx)

        if self._n_frames == 0 or frame_idx >= self._n_frames:
            return {}
        self.services.clock.tick(frame_idx)

        pos = (
            float(self._flight_x[frame_idx]),
            float(self._flight_y[frame_idx]),
            float(self._flight_z[frame_idx]),
        )
        if self._prev_pos is None:
            vel = (
                float(self._flight_vx[frame_idx]),
                float(self._flight_vy[frame_idx]),
                float(self._flight_vz[frame_idx]),
            )
        else:
            dt_s = max(float(_cfg.SIM_DT_MS) / 1000.0, 1e-6)
            vel = (
                (pos[0] - self._prev_pos[0]) / dt_s,
                (pos[1] - self._prev_pos[1]) / dt_s,
                (pos[2] - self._prev_pos[2]) / dt_s,
            )
        self._prev_pos = pos
        self.runtime.flight.frame = int(frame_idx)
        self.runtime.flight.plane_pos = pos
        self.runtime.flight.plane_vel = vel

        decision_state = self._decision_state
        if decision_state is not None:
            decision = self._decision_director.step(frame_idx, decision_state)
            if decision.fire_bullets:
                engagement.spawn_burst(
                    pos,
                    vel,
                    bullets=_cfg.BULLET_BURST,
                    rng=self._engagement_rng,
                )
            if decision.launch_rocket:
                engagement.spawn_rocket()
            if decision.drop_bomb:
                engagement.spawn_bomb()

        self._apply_terrain_impacts(
            frame_idx,
            self.runtime.active_rockets,
            weapon="rocket",
            scale=_ROCKET_EXPLOSION_SCALE,
        )
        self._apply_terrain_impacts(
            frame_idx,
            self.runtime.active_bombs,
            weapon="bomb",
            scale=_BOMB_EXPLOSION_SCALE,
            style="mushroom",
        )
        self.runtime.active_bullets.step()
        self.runtime.active_rockets.step()
        self.runtime.active_bombs.step()
        if self._mission_runtime is not None:
            result = self._mission_runtime.tick(self.runtime)
            self._mission_result = result
            self._apply_mission_directives(frame_idx, result.directives)
        return {}

    @property
    def mission_result(self) -> MissionTickResult | None:
        return self._mission_result

    def apply_terrain_impacts(
        self,
        frame: int,
        buffer: Any,
        *,
        weapon: str,
        scale: float,
        style: str | None = None,
    ) -> None:
        self._apply_terrain_impacts(
            frame,
            buffer,
            weapon=weapon,
            scale=scale,
            style=style,
        )

    def _apply_terrain_impacts(
        self,
        frame: int,
        buffer: Any,
        *,
        weapon: str,
        scale: float,
        style: str | None = None,
    ) -> None:
        xs, ys, zs, rows = buffer.sample_positions()
        if rows.size == 0:
            return
        ground = np.asarray(sample_height(xs, ys, default=0.0), dtype=np.float32)
        impact = zs <= ground
        if not impact.any():
            return
        for x, y, z in zip(xs[impact], ys[impact], ground[impact]):
            self.runtime.impacts.append(
                ImpactEvent(
                    frame=int(frame),
                    x=float(x),
                    y=float(y),
                    z=float(z),
                    target="terrain",
                    weapon=weapon,
                )
            )
            self.runtime.explosions.append(
                ExplosionEvent(
                    frame=int(frame),
                    x=float(x),
                    y=float(y),
                    z=float(z),
                    scale=float(scale),
                    style=style,
                )
            )
        buffer.remove(rows[impact])

    def _apply_mission_directives(
        self,
        frame: int,
        directives: tuple[MissionDirective, ...],
    ) -> None:
        if not directives:
            return
        for directive in directives:
            payload: dict[str, object] = {
                "kind": directive.kind,
                "payload": dict(directive.payload),
            }
            self.runtime.debug_events.append(
                DebugEvent(
                    frame=int(frame),
                    kind="mission",
                    payload=payload,
                )
            )


def determinism_hash(runtime: RuntimeState, samples: list[tuple[float, float, float]]) -> str:
    payload: dict[str, Any] = {
        "samples": samples,
        "impacts": [event.to_dict() for event in runtime.impacts],
        "explosions": [event.to_dict() for event in runtime.explosions],
        "parachutes": [event.to_dict() for event in runtime.parachutes],
    }
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def summarize(runtime: RuntimeState, frames: int, samples: list[tuple[float, float, float]]) -> SimSummary:
    return SimSummary(
        frames=frames,
        impacts=len(runtime.impacts),
        explosions=len(runtime.explosions),
        parachutes=len(runtime.parachutes),
        hash=determinism_hash(runtime, samples),
    )


__all__ = [
    "Simulation",
    "SimSummary",
    "determinism_hash",
    "summarize",
]
