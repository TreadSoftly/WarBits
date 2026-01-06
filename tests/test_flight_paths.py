import random
import unittest

import numpy as np

from warbits.logic.flight_paths import build_flight_plan


class TestFlightPaths(unittest.TestCase):
    def test_default_plan_deterministic(self) -> None:
        x1, y1, z1, slices1 = build_flight_plan()
        x2, y2, z2, slices2 = build_flight_plan()
        self.assertTrue(np.array_equal(x1, x2))
        self.assertTrue(np.array_equal(y1, y2))
        self.assertTrue(np.array_equal(z1, z2))
        self.assertEqual(slices1, slices2)

    def test_seeded_plan_deterministic(self) -> None:
        rng1 = random.Random(123)
        rng2 = random.Random(123)
        x1, y1, z1, slices1 = build_flight_plan(rng=rng1)
        x2, y2, z2, slices2 = build_flight_plan(rng=rng2)
        self.assertTrue(np.array_equal(x1, x2))
        self.assertTrue(np.array_equal(y1, y2))
        self.assertTrue(np.array_equal(z1, z2))
        self.assertEqual(slices1, slices2)

    def test_variant_plan_lengths_match(self) -> None:
        x_base, y_base, z_base, slices_base = build_flight_plan()
        rng = random.Random(7)
        x_var, y_var, z_var, slices_var = build_flight_plan(rng=rng)
        self.assertEqual(len(x_base), len(x_var))
        self.assertEqual(len(y_base), len(y_var))
        self.assertEqual(len(z_base), len(z_var))
        self.assertEqual(slices_base, slices_var)
