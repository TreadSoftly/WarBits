import os
import unittest
from unittest import mock

import numpy as np

from warbits.logic.aircraft_hits import check_aircraft_hits
from warbits.logic.state import RUNTIME


class TestAircraftHits(unittest.TestCase):
    def setUp(self) -> None:
        RUNTIME.active_rockets.clear()
        RUNTIME.active_bombs.clear()
        RUNTIME.impacts.clear()

    def test_rocket_hit_records_impact(self) -> None:
        traj_x = np.array([-200.0, 0.0, 200.0], dtype=np.float32)
        zeros = np.array([0.0, 0.0, 0.0], dtype=np.float32)
        RUNTIME.active_rockets.add(traj_x, zeros, zeros)
        RUNTIME.active_rockets.step()
        RUNTIME.active_rockets.step()

        check_aircraft_hits(0, (0.0, 0.0, 0.0))

        self.assertEqual(len(RUNTIME.active_rockets), 0)
        self.assertEqual(len(RUNTIME.impacts), 1)
        event = RUNTIME.impacts[0]
        self.assertEqual(event["weapon"], "rocket")
        self.assertEqual(event["target"], "aircraft")

    def test_bomb_hit_records_impact(self) -> None:
        traj_x = np.array(
            [-300.0, -200.0, -100.0, 0.0, 100.0, 200.0, 300.0],
            dtype=np.float32,
        )
        zeros = np.zeros_like(traj_x, dtype=np.float32)
        RUNTIME.active_bombs.add(traj_x, zeros, zeros)
        for _ in range(6):
            RUNTIME.active_bombs.step()

        with mock.patch.dict(os.environ, {"WARBITS_AIRCRAFT_BOMB_HITS": "1"}):
            check_aircraft_hits(0, (0.0, 0.0, 0.0))

        self.assertEqual(len(RUNTIME.active_bombs), 0)
        self.assertEqual(len(RUNTIME.impacts), 1)
        event = RUNTIME.impacts[0]
        self.assertEqual(event["weapon"], "bomb")
        self.assertEqual(event["target"], "aircraft")
