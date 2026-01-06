import unittest
from typing import Any, cast

import numpy as np

from warbits.core.sim import Simulation
from warbits.logic.state import RUNTIME, RuntimeState
from warbits.physics import ballistics, bombs, rockets, terrain


class _DummyScatter:
    _offsets3d: tuple[list[float], list[float], list[float]]

    def __init__(self) -> None:
        self._offsets3d = ([], [], [])

    def set_visible(self, _visible: bool) -> None:
        return None


class _DummyAxes:
    def scatter(self, *_args: object, **_kwargs: object) -> _DummyScatter:
        return _DummyScatter()


class TestPhysics(unittest.TestCase):
    def test_bullet_hits_ground(self) -> None:
        _x, _y, z = ballistics.simulate_bullet_trajectory(
            (0.0, 0.0, 50.0),
            (0.0, 0.0, 0.0),
            dt=0.1,
            max_time=10.0,
        )
        self.assertGreater(z[0], 0.0)
        self.assertTrue(np.any(z <= 0.0))
        self.assertTrue(np.isclose(float(z[-1]), 0.0, atol=1e-6))

    def test_bomb_hits_ground(self) -> None:
        _x, _y, z = bombs.simulate_bomb_trajectory(
            (0.0, 0.0, 100.0),
            (0.0, 0.0, 0.0),
            dt=0.5,
            max_time=20.0,
        )
        self.assertGreater(z[0], 0.0)
        self.assertTrue(np.any(z <= 0.0))
        self.assertTrue(np.isclose(float(z[-1]), 0.0, atol=1e-6))

    def test_rocket_hits_ground(self) -> None:
        _x, _y, z = rockets.simulate_rocket_trajectory(
            (0.0, 0.0, 50.0),
            (0.0, 0.0, 0.0),
            dt=0.1,
            max_time=5.0,
        )
        self.assertGreater(z[0], 0.0)
        self.assertTrue(np.any(z <= 0.0))
        self.assertTrue(np.isclose(float(z[-1]), 0.0, atol=1e-6))

    def test_bullet_start_below_ground_clamps(self) -> None:
        _x, _y, z = ballistics.simulate_bullet_trajectory(
            (0.0, 0.0, -10.0),
            (0.0, 0.0, 0.0),
            dt=0.1,
            max_time=1.0,
        )
        self.assertTrue(np.allclose(z, 0.0, atol=1e-6))

    def test_rocket_start_below_ground_clamps(self) -> None:
        _x, _y, z = rockets.simulate_rocket_trajectory(
            (0.0, 0.0, -5.0),
            (0.0, 0.0, 0.0),
            dt=0.1,
            max_time=1.0,
        )
        self.assertTrue(np.allclose(z, 0.0, atol=1e-6))

    def test_bullet_hits_terrain_height(self) -> None:
        x_grid = np.array([[0.0, 1.0], [0.0, 1.0]])
        y_grid = np.array([[0.0, 0.0], [1.0, 1.0]])
        z_grid = np.full((2, 2), 50.0)
        terrain.set_active_terrain(x_grid, y_grid, z_grid)
        try:
            RUNTIME.active_bullets.clear()
            RUNTIME.impacts.clear()
            RUNTIME.explosions.clear()
            RUNTIME.active_bullets.add(
                np.array([0.5], dtype=np.float32),
                np.array([0.5], dtype=np.float32),
                np.array([10.0], dtype=np.float32),
            )
            ballistics.update(0, cast(Any, _DummyAxes()))
            self.assertEqual(len(RUNTIME.active_bullets), 0)
        finally:
            terrain.set_active_terrain(
                np.empty((0, 0)), np.empty((0, 0)), np.empty((0, 0))
            )

    def test_rocket_hits_terrain_height(self) -> None:
        x_grid = np.array([[0.0, 1.0], [0.0, 1.0]])
        y_grid = np.array([[0.0, 0.0], [1.0, 1.0]])
        z_grid = np.full((2, 2), 25.0)
        terrain.set_active_terrain(x_grid, y_grid, z_grid)
        try:
            runtime = RuntimeState()
            sim = Simulation(runtime=runtime, step_callback=lambda _frame: {})
            runtime.active_rockets.add(
                np.array([0.5], dtype=np.float32),
                np.array([0.5], dtype=np.float32),
                np.array([10.0], dtype=np.float32),
            )
            sim.apply_terrain_impacts(
                0,
                runtime.active_rockets,
                weapon="rocket",
                scale=1.0,
            )
            self.assertEqual(len(runtime.active_rockets), 0)
            self.assertEqual(len(runtime.impacts), 1)
            self.assertEqual(len(runtime.explosions), 1)
            self.assertAlmostEqual(float(runtime.impacts[0].z), 25.0, places=6)
        finally:
            terrain.set_active_terrain(
                np.empty((0, 0)), np.empty((0, 0)), np.empty((0, 0))
            )

    def test_bomb_hits_terrain_height(self) -> None:
        x_grid = np.array([[0.0, 1.0], [0.0, 1.0]])
        y_grid = np.array([[0.0, 0.0], [1.0, 1.0]])
        z_grid = np.full((2, 2), 30.0)
        terrain.set_active_terrain(x_grid, y_grid, z_grid)
        try:
            runtime = RuntimeState()
            sim = Simulation(runtime=runtime, step_callback=lambda _frame: {})
            runtime.active_bombs.add(
                np.array([0.5], dtype=np.float32),
                np.array([0.5], dtype=np.float32),
                np.array([5.0], dtype=np.float32),
            )
            sim.apply_terrain_impacts(
                0,
                runtime.active_bombs,
                weapon="bomb",
                scale=1.0,
                style="mushroom",
            )
            self.assertEqual(len(runtime.active_bombs), 0)
            self.assertEqual(len(runtime.impacts), 1)
            self.assertEqual(len(runtime.explosions), 1)
            self.assertAlmostEqual(float(runtime.impacts[0].z), 30.0, places=6)
            self.assertEqual(runtime.explosions[0].style, "mushroom")
        finally:
            terrain.set_active_terrain(
                np.empty((0, 0)), np.empty((0, 0)), np.empty((0, 0))
            )
