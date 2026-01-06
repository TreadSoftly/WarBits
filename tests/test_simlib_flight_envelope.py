import math
import unittest

from warbits.simlib.flight.envelope import (
    coordinated_turn_rate_rad_s,
    compute_flight_limits,
    max_bank_for_load_factor_rad,
    stall_speed_mps,
)
from warbits.simlib.flight.types import AircraftPerformance


class TestSimlibFlightEnvelope(unittest.TestCase):
    def test_stall_speed_formula(self) -> None:
        v = stall_speed_mps(
            mass_kg=10_000.0,
            wing_area_m2=50.0,
            cl_max=1.5,
            rho_kg_m3=1.225,
        )
        self.assertAlmostEqual(v, 46.2037, places=3)

    def test_max_bank_from_g(self) -> None:
        bank = max_bank_for_load_factor_rad(3.0)
        self.assertAlmostEqual(math.degrees(bank), 70.5288, places=3)

    def test_turn_rate(self) -> None:
        omega = coordinated_turn_rate_rad_s(200.0, math.radians(60.0))
        self.assertAlmostEqual(omega, 0.08493, places=4)

    def test_compute_limits_respects_g(self) -> None:
        perf = AircraftPerformance(
            min_speed_mps=90.0,
            max_g=3.0,
            max_bank_deg=80.0,  # would imply > 3g if fully used in level turn
        )
        limits = compute_flight_limits(perf, rho_kg_m3=1.225)
        # Should be clamped to the ~70.5deg implied by 3g.
        self.assertAlmostEqual(math.degrees(limits.max_bank_rad), 70.5288, places=3)
        self.assertEqual(limits.min_speed_mps, 90.0)

    def test_compute_limits_stall_margin(self) -> None:
        perf = AircraftPerformance(mass_kg=10_000.0, wing_area_m2=50.0, cl_max=1.5)
        limits = compute_flight_limits(perf, rho_kg_m3=1.225, stall_margin=1.15)
        # Stall ~46.2037 -> min ~53.134
        self.assertAlmostEqual(limits.min_speed_mps, 53.134, places=2)


if __name__ == "__main__":
    unittest.main()
