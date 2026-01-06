import unittest
import numpy as np

from warbits.simlib.math3d import unit, distance_point_segment, distance_point_segment_batch


class TestMath3D(unittest.TestCase):
    def test_unit_zero(self):
        v = np.array([0.0, 0.0, 0.0], dtype=float)
        u = unit(v)
        self.assertTrue(np.allclose(u, np.zeros(3)))

    def test_distance_point_segment(self):
        p = np.array([1.0, 1.0, 0.0], dtype=float)
        a = np.array([0.0, 0.0, 0.0], dtype=float)
        b = np.array([2.0, 0.0, 0.0], dtype=float)
        d = distance_point_segment(p, a, b)
        self.assertAlmostEqual(d, 1.0, places=6)

    def test_distance_batch(self):
        p = np.array([0.0, 1.0, 0.0], dtype=float)
        a = np.array([[0.0, 0.0, 0.0], [10.0, 0.0, 0.0]], dtype=float)
        b = np.array([[0.0, 0.0, 0.0], [10.0, 2.0, 0.0]], dtype=float)
        ds = distance_point_segment_batch(p, a, b)
        self.assertEqual(ds.shape, (2,))
        self.assertAlmostEqual(float(ds[0]), 1.0, places=6)
        self.assertAlmostEqual(float(ds[1]), 10.0, places=6)


if __name__ == "__main__":
    unittest.main()
