import unittest
import numpy as np

from warbits.simlib.guidance import pure_pursuit_direction, lead_pursuit_direction, proportional_navigation_accel


class TestGuidance(unittest.TestCase):
    def test_pure_pursuit(self):
        own = np.array([0.0, 0.0, 0.0])
        tgt = np.array([10.0, 0.0, 0.0])
        d = pure_pursuit_direction(own, tgt)
        self.assertTrue(np.allclose(d, np.array([1.0, 0.0, 0.0])))

    def test_lead_pursuit_fallback(self):
        own = np.array([0.0, 0.0, 0.0])
        tgt = np.array([10.0, 0.0, 0.0])
        tv = np.array([0.0, 0.0, 0.0])
        d = lead_pursuit_direction(own, 0.0, tgt, tv)
        # If own speed is zero, it should just point to target
        self.assertTrue(np.allclose(d, np.array([1.0, 0.0, 0.0])))

    def test_pn_zero_when_same_pos(self):
        own = np.array([0.0, 0.0, 0.0])
        tgt = np.array([0.0, 0.0, 0.0])
        a = proportional_navigation_accel(own, np.zeros(3), tgt, np.zeros(3))
        self.assertTrue(np.allclose(a, np.zeros(3)))


if __name__ == "__main__":
    unittest.main()
