import unittest

from warbits.simlib.rng import DeterministicRNG, stable_seed_u64


class TestDeterministicRNG(unittest.TestCase):
    def test_stable_seed(self):
        self.assertEqual(stable_seed_u64("abc"), stable_seed_u64("abc"))
        self.assertNotEqual(stable_seed_u64("abc"), stable_seed_u64("abcd"))

    def test_stream_advances(self):
        rng = DeterministicRNG.from_seed(123)
        a = rng.uniform()
        b = rng.uniform()
        self.assertNotEqual(a, b)

    def test_split_independent_of_draw_order(self):
        base1 = DeterministicRNG.from_seed("scenario")
        # Draw from base1 before split
        _ = base1.uniform()
        child1 = base1.split("weapons")

        base2 = DeterministicRNG.from_seed("scenario")
        child2 = base2.split("weapons")

        self.assertEqual(child1.root_seed_u64, child2.root_seed_u64)
        # And child streams produce same sequence
        self.assertEqual(child1.uniform(), child2.uniform())
        self.assertEqual(child1.uniform(), child2.uniform())


if __name__ == "__main__":
    unittest.main()
