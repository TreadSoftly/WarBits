import unittest

from warbits.simlib.atmosphere import isa_density_kg_m3, isa_temperature_k


class TestAtmosphereISA(unittest.TestCase):
    def test_sea_level_density(self):
        rho0 = float(isa_density_kg_m3(0.0))
        self.assertAlmostEqual(rho0, 1.225, places=3)

    def test_density_decreases(self):
        rho0 = float(isa_density_kg_m3(0.0))
        rho5k = float(isa_density_kg_m3(5000.0))
        rho10k = float(isa_density_kg_m3(10000.0))
        self.assertGreater(rho0, rho5k)
        self.assertGreater(rho5k, rho10k)

    def test_tropopause_temperature(self):
        t11 = float(isa_temperature_k(11000.0))
        self.assertAlmostEqual(t11, 216.65, places=2)


if __name__ == "__main__":
    unittest.main()
