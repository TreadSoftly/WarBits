import unittest

from warbits.simlib.spatial_hash import SpatialHash3D


class TestSpatialHash(unittest.TestCase):
    def test_insert_query(self):
        sh = SpatialHash3D(cell_size=10.0)
        sh.insert(1, 0.0, 0.0, 0.0)
        sh.insert(2, 50.0, 0.0, 0.0)
        near = sh.query_radius(1.0, 1.0, 0.0, radius=15.0)
        self.assertIn(1, near)
        self.assertNotIn(2, near)

        far = sh.query_radius(49.0, 0.0, 0.0, radius=5.0)
        self.assertIn(2, far)
        self.assertNotIn(1, far)


if __name__ == "__main__":
    unittest.main()
