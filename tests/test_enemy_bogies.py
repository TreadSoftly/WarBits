import os
import unittest

import numpy as np

os.environ.setdefault("MPLBACKEND", "Agg")

from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure

from warbits.logic import enemy_bogies
from warbits.logic.flight_paths import build_flight_plan
from warbits.logic.state import RUNTIME
from warbits.physics.terrain import set_active_terrain


class TestEnemyBogies(unittest.TestCase):
    def setUp(self) -> None:
        RUNTIME.active_bullets.clear()
        RUNTIME.active_rockets.clear()
        RUNTIME.active_bombs.clear()
        RUNTIME.impacts.clear()
        enemy_bogies.reset()

    def test_update_records_impact(self) -> None:
        fig = Figure()
        FigureCanvas(fig)
        ax = fig.add_subplot(111, projection="3d")
        x = np.array([[0.0, 1.0], [0.0, 1.0]], dtype=np.float64)
        y = np.array([[0.0, 0.0], [1.0, 1.0]], dtype=np.float64)
        z = np.zeros((2, 2), dtype=np.float64)
        set_active_terrain(x, y, z)
        flight_x, flight_y, flight_z, slices = build_flight_plan()
        enemy_bogies.init(
            ax,
            flight_x,
            flight_y,
            flight_z,
            slices,
            appear_at=0,
            closing_factor=0.2,
            hit_frame=None,
        )

        enemy_bogies.update(0)
        pos = enemy_bogies.get_position(0)
        self.assertIsNotNone(pos)
        bx, by, bz = pos or (0.0, 0.0, 0.0)
        traj_x = np.array([bx - 200.0, bx + 200.0], dtype=np.float32)
        traj_y = np.array([by, by], dtype=np.float32)
        traj_z = np.array([bz, bz], dtype=np.float32)
        RUNTIME.active_bullets.add(traj_x, traj_y, traj_z)
        RUNTIME.active_bullets.step()
        enemy_bogies.update(0)

        self.assertGreaterEqual(len(RUNTIME.impacts), 1)
        event = RUNTIME.impacts[0]
        self.assertEqual(event["weapon"], "bullet")
        self.assertEqual(event["target"], "bogie")

        fig.clear()
        set_active_terrain(np.empty((0, 0)), np.empty((0, 0)), np.empty((0, 0)))

    def test_configure_without_escape_slice(self) -> None:
        fig = Figure()
        FigureCanvas(fig)
        ax = fig.add_subplot(111, projection="3d")
        flight_x = np.linspace(0.0, 100.0, 5, dtype=np.float64)
        flight_y = np.linspace(0.0, 100.0, 5, dtype=np.float64)
        flight_z = np.full(5, 1000.0, dtype=np.float64)
        slices = {"Approach": (0, 5)}
        enemy_bogies.init(ax, flight_x, flight_y, flight_z, slices)
        pos = enemy_bogies.get_position(0)
        self.assertIsNotNone(pos)
        fig.clear()
