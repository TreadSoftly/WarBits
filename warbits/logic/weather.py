from __future__ import annotations

from dataclasses import dataclass
import math
import random
import secrets

Vector3 = tuple[float, float, float]


@dataclass(frozen=True)
class WeatherState:
    seed: int
    wind: Vector3
    gust: Vector3
    turbulence: float
    visibility_km: float


@dataclass(frozen=True)
class WeatherConfig:
    wind_speed_mps: tuple[float, float] = (0.0, 25.0)
    wind_dir_deg: tuple[float, float] = (0.0, 360.0)
    vertical_wind_mps: tuple[float, float] = (-2.0, 2.0)
    gust_factor: tuple[float, float] = (0.0, 0.4)
    turbulence: tuple[float, float] = (0.0, 1.0)
    visibility_km: tuple[float, float] = (8.0, 35.0)


class WeatherDirector:
    def __init__(self, *, seed: int | None = None, config: WeatherConfig | None = None) -> None:
        self._seed = seed
        self._config = config or WeatherConfig()

    def build(self, *, seed: int | None = None) -> WeatherState:
        if seed is None:
            seed = self._seed if self._seed is not None else secrets.randbits(32)
        rng = random.Random(seed)
        cfg = self._config

        speed = rng.uniform(*cfg.wind_speed_mps)
        direction = math.radians(rng.uniform(*cfg.wind_dir_deg))
        wind_x = math.cos(direction) * speed
        wind_y = math.sin(direction) * speed
        wind_z = rng.uniform(*cfg.vertical_wind_mps)

        gust_factor = rng.uniform(*cfg.gust_factor)
        gust = (wind_x * gust_factor, wind_y * gust_factor, wind_z * gust_factor)
        turbulence = rng.uniform(*cfg.turbulence)
        visibility = rng.uniform(*cfg.visibility_km)

        return WeatherState(
            seed=int(seed),
            wind=(wind_x, wind_y, wind_z),
            gust=gust,
            turbulence=turbulence,
            visibility_km=visibility,
        )


__all__ = [
    "WeatherConfig",
    "WeatherDirector",
    "WeatherState",
]
