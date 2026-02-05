import unittest

from warbits.simlib.ai.rng import DeterministicRNG, stable_hash64


class TestDeterministicRNG(unittest.TestCase):
    def test_same_seed_same_sequence(self):
        r1 = DeterministicRNG(1234)
        r2 = DeterministicRNG(1234)
        a1 = [float(r1.uniform(0, 1)) for _ in range(5)]
        a2 = [float(r2.uniform(0, 1)) for _ in range(5)]
        self.assertEqual(a1, a2)

    def test_fork_stable(self):
        r = DeterministicRNG(999)
        a = r.fork("entity", "bogie-1").integers(0, 100, size=10).tolist()
        b = r.fork("entity", "bogie-1").integers(0, 100, size=10).tolist()
        c = r.fork("entity", "bogie-2").integers(0, 100, size=10).tolist()
        self.assertEqual(a, b)
        self.assertNotEqual(a, c)

    def test_stable_hash(self):
        h1 = stable_hash64("A", 1, 2.0, True, None)
        h2 = stable_hash64("A", 1, 2.0, True, None)
        h3 = stable_hash64("A", 1, 2.0, False, None)
        self.assertEqual(h1, h2)
        self.assertNotEqual(h1, h3)


if __name__ == "__main__":
    unittest.main()
