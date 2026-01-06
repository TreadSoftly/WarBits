import unittest
import numpy as np

from warbits.visual.panda3d.camera import ChaseCameraConfig, compute_chase_camera_pose
from warbits.visual.panda3d.terrain import HeightfieldSpec, build_wire_grid_segments, compute_vertex_normals


class TestP3DHelpersPureMath(unittest.TestCase):
    def test_compute_chase_camera_pose_shapes(self):
        cfg = ChaseCameraConfig(distance=10.0, height=2.0, look_ahead=3.0, smoothing_tau=0.1)
        cam, look = compute_chase_camera_pose(
            np.array([1.0, 2.0, 3.0], dtype=np.float32),
            np.array([5.0, 0.0, 0.0], dtype=np.float32),
            cfg=cfg,
        )
        self.assertEqual(cam.shape, (3,))
        self.assertEqual(look.shape, (3,))

    def test_wire_grid_segments_count_nonzero(self):
        h = np.zeros((10, 10), dtype=np.float32)
        spec = HeightfieldSpec(h, x0=0.0, y0=0.0, dx=1.0, dy=1.0)
        segs = build_wire_grid_segments(spec, stride=2)
        # We should have some segments.
        self.assertGreater(segs.shape[0], 0)
        self.assertEqual(segs.shape[1:], (2, 3))

    def test_normals_unit_length(self):
        h = np.random.default_rng(0).normal(size=(20, 20)).astype(np.float32)
        n = compute_vertex_normals(h, dx=1.0, dy=1.0)
        mags = np.linalg.norm(n.reshape(-1, 3), axis=1)
        self.assertTrue(np.all(np.isfinite(mags)))
        # Should be close to 1
        self.assertLess(np.max(np.abs(mags - 1.0)), 1e-3)


if __name__ == "__main__":
    unittest.main()
