import unittest

import numpy as np

from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure

from warbits.logic import enemy_ground
from warbits.logic.state import RUNTIME


class TestEnemyGround(unittest.TestCase):
    def setUp(self) -> None:
        RUNTIME.active_bullets.clear()
        RUNTIME.active_rockets.clear()
        RUNTIME.active_bombs.clear()
        RUNTIME.impacts.clear()

    def test_check_hits_records_impact(self) -> None:
        fig = Figure()
        FigureCanvas(fig)
        ax = fig.add_subplot(111, projection="3d")
        enemy_ground.init(ax)
        enemy_ground.configure(0)
        enemy_ground.reset()
        enemy_ground.update(0, 0.0, 0.0)

        gx, gy, gz = enemy_ground._emplacements[0].center  # type: ignore[attr-defined]
        traj_x = np.array([gx - 200.0, gx + 200.0], dtype=np.float32)
        traj_y = np.array([gy, gy], dtype=np.float32)
        traj_z = np.array([gz, gz], dtype=np.float32)
        RUNTIME.active_bullets.add(traj_x, traj_y, traj_z)
        RUNTIME.active_bullets.step()
        enemy_ground.check_hits(0)

        self.assertTrue(enemy_ground._emplacements[0].destroyed)  # type: ignore[attr-defined]
        self.assertEqual(len(RUNTIME.impacts), 1)
        event = RUNTIME.impacts[0]
        self.assertEqual(event["weapon"], "bullet")
        self.assertEqual(event["target"], "aaa_0")

        fig.clear()
