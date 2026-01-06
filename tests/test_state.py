import unittest

import numpy as np

from warbits.config import settings as _cfg
from warbits.logic.state import ProjectileBuffer


class TestProjectileBuffer(unittest.TestCase):
    def test_capacity_overflow_raises(self) -> None:
        buf = ProjectileBuffer(capacity=2, max_samples=3)
        with self.assertRaises(ValueError):
            buf.add(
                np.zeros((3, 3)),
                np.zeros((3, 3)),
                np.zeros((3, 3)),
            )

    def test_overwrite_keeps_capacity(self) -> None:
        buf = ProjectileBuffer(capacity=2, max_samples=3)
        buf.add(np.zeros(3), np.zeros(3), np.zeros(3))
        buf.add(np.ones(3), np.ones(3), np.ones(3))
        buf.add(np.full(3, 2.0), np.full(3, 2.0), np.full(3, 2.0))
        self.assertLessEqual(len(buf), 2)
        xs, ys, zs, _ = buf.sample_positions()
        self.assertEqual(set(xs.tolist()), {1.0, 2.0})
        self.assertEqual(set(ys.tolist()), {1.0, 2.0})
        self.assertEqual(set(zs.tolist()), {1.0, 2.0})

    def test_max_samples_autoresize(self) -> None:
        buf = ProjectileBuffer(capacity=1, max_samples=2)
        resize_prev = _cfg.PROJECTILE_AUTO_RESIZE
        strict_prev = _cfg.STRICT_PHYSICS
        try:
            _cfg.PROJECTILE_AUTO_RESIZE = True
            _cfg.STRICT_PHYSICS = False
            buf.add(np.arange(4, dtype=np.float32), np.arange(4, dtype=np.float32), np.arange(4, dtype=np.float32))
            self.assertGreaterEqual(buf.max_samples, 4)
            self.assertEqual(int(buf.lengths[0]), 4)
        finally:
            _cfg.PROJECTILE_AUTO_RESIZE = resize_prev
            _cfg.STRICT_PHYSICS = strict_prev

    def test_max_samples_truncates_when_disabled(self) -> None:
        buf = ProjectileBuffer(capacity=1, max_samples=2)
        resize_prev = _cfg.PROJECTILE_AUTO_RESIZE
        strict_prev = _cfg.STRICT_PHYSICS
        try:
            _cfg.PROJECTILE_AUTO_RESIZE = False
            _cfg.STRICT_PHYSICS = False
            buf.add(
                np.array([1.0, 2.0, 3.0], dtype=np.float32),
                np.array([1.0, 2.0, 3.0], dtype=np.float32),
                np.array([1.0, 2.0, 3.0], dtype=np.float32),
            )
            self.assertEqual(int(buf.lengths[0]), 2)
            self.assertEqual(float(buf.paths[0, 0, 1]), 2.0)
        finally:
            _cfg.PROJECTILE_AUTO_RESIZE = resize_prev
            _cfg.STRICT_PHYSICS = strict_prev
