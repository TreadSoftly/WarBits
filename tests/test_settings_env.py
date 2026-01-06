import importlib
import os
import unittest
from typing import Protocol, cast

from warbits.config import settings as _settings

_ENV_KEYS = [
    "WARBITS_WIND_X",
    "WARBITS_WIND_Y",
    "WARBITS_WIND_Z",
    "WARBITS_BULLET_DRAG",
    "WARBITS_ROCKET_DRAG",
    "WARBITS_BOMB_DRAG",
    "WARBITS_PARACHUTE_DRAG_CLOSED",
    "WARBITS_PARACHUTE_DRAG_OPEN",
    "WARBITS_TERRAIN_XMIN",
    "WARBITS_TERRAIN_XMAX",
    "WARBITS_TERRAIN_YMIN",
    "WARBITS_TERRAIN_YMAX",
    "WARBITS_TERRAIN_FIT_SCREEN",
    "WARBITS_TERRAIN_FORCE_SQUARE",
]


class _Settings(Protocol):
    WIND_X: float
    WIND_Y: float
    WIND_Z: float
    BULLET_DRAG: float
    ROCKET_DRAG: float
    BOMB_DRAG: float
    PARACHUTE_DRAG_CLOSED: float
    PARACHUTE_DRAG_OPEN: float
    TERRAIN_XMIN: float
    TERRAIN_XMAX: float
    TERRAIN_YMIN: float
    TERRAIN_YMAX: float


def _reload_settings() -> _Settings:
    return cast(_Settings, importlib.reload(_settings))


class TestSettingsEnv(unittest.TestCase):
    def setUp(self) -> None:
        self._env_backup = {key: os.environ.get(key) for key in _ENV_KEYS}

    def tearDown(self) -> None:
        for key, value in self._env_backup.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        importlib.reload(_settings)

    def test_negative_wind_allowed(self) -> None:
        os.environ["WARBITS_WIND_X"] = "-5.5"
        os.environ["WARBITS_WIND_Y"] = "3.25"
        os.environ["WARBITS_WIND_Z"] = "-0.75"
        cfg = _reload_settings()
        self.assertEqual(cfg.WIND_X, -5.5)
        self.assertEqual(cfg.WIND_Y, 3.25)
        self.assertEqual(cfg.WIND_Z, -0.75)

    def test_zero_drag_allowed(self) -> None:
        os.environ["WARBITS_BULLET_DRAG"] = "0"
        os.environ["WARBITS_ROCKET_DRAG"] = "0"
        os.environ["WARBITS_BOMB_DRAG"] = "0"
        os.environ["WARBITS_PARACHUTE_DRAG_CLOSED"] = "0"
        os.environ["WARBITS_PARACHUTE_DRAG_OPEN"] = "0"
        cfg = _reload_settings()
        self.assertEqual(cfg.BULLET_DRAG, 0.0)
        self.assertEqual(cfg.ROCKET_DRAG, 0.0)
        self.assertEqual(cfg.BOMB_DRAG, 0.0)
        self.assertEqual(cfg.PARACHUTE_DRAG_CLOSED, 0.0)
        self.assertEqual(cfg.PARACHUTE_DRAG_OPEN, 0.0)

    def test_negative_terrain_bounds_allowed(self) -> None:
        os.environ["WARBITS_TERRAIN_FIT_SCREEN"] = "0"
        os.environ["WARBITS_TERRAIN_FORCE_SQUARE"] = "0"
        os.environ["WARBITS_TERRAIN_XMIN"] = "-1000"
        os.environ["WARBITS_TERRAIN_XMAX"] = "1000"
        os.environ["WARBITS_TERRAIN_YMIN"] = "-2000"
        os.environ["WARBITS_TERRAIN_YMAX"] = "2000"
        cfg = _reload_settings()
        self.assertEqual(cfg.TERRAIN_XMIN, -1000.0)
        self.assertEqual(cfg.TERRAIN_XMAX, 1000.0)
        self.assertEqual(cfg.TERRAIN_YMIN, -2000.0)
        self.assertEqual(cfg.TERRAIN_YMAX, 2000.0)
