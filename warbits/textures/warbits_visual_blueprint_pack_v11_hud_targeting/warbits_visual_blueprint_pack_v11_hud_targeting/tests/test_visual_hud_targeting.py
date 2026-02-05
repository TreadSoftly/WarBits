import unittest

import numpy as np

from warbits.visual.hud.targeting import lead_solution_simple, solve_intercept_no_gravity


class TestHudTargeting(unittest.TestCase):
    def test_intercept_no_gravity_stationary(self):
        shooter = np.array([0.0, 0.0, 0.0])
        target = np.array([1000.0, 0.0, 0.0])
        v = np.array([0.0, 0.0, 0.0])
        t = solve_intercept_no_gravity(shooter, target, v, projectile_speed_mps=500.0)
        self.assertIsNotNone(t)
        assert t is not None
        t_val = float(t)
        self.assertAlmostEqual(t_val, 2.0, places=6)

    def test_intercept_no_gravity_moving(self):
        shooter = np.array([0.0, 0.0, 0.0])
        target = np.array([1000.0, 0.0, 0.0])
        v = np.array([0.0, 100.0, 0.0])
        t = solve_intercept_no_gravity(shooter, target, v, projectile_speed_mps=500.0)
        self.assertIsNotNone(t)
        assert t is not None
        t_val = float(t)
        self.assertGreater(t_val, 2.0)

    def test_lead_solution_has_unit_direction(self):
        shooter = np.array([0.0, 0.0, 1000.0])
        shooter_vel = np.array([200.0, 0.0, 0.0])
        target = np.array([2000.0, 500.0, 1000.0])
        target_vel = np.array([150.0, 0.0, 0.0])
        sol = lead_solution_simple(shooter, shooter_vel, target, target_vel, projectile_speed_mps=900.0)
        self.assertIsNotNone(sol)
        assert sol is not None
        n = float(np.linalg.norm(sol.aim_direction_unit))
        self.assertAlmostEqual(n, 1.0, places=6)


if __name__ == "__main__":
    unittest.main()
if __name__ == "__main__":
    unittest.main()
    unittest.main()
