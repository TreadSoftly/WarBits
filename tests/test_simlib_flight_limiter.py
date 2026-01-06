import math
import unittest

import numpy as np

from warbits.simlib.flight.envelope import compute_flight_limits
from warbits.simlib.flight.limiter import limit_velocity_vector
from warbits.simlib.flight.types import AircraftPerformance
from warbits.simlib.math3d import angle_between, safe_unit


class TestSimlibFlightLimiter(unittest.TestCase):
    def test_turn_rate_is_limited(self) -> None:
        perf = AircraftPerformance(
            min_speed_mps=80.0,
            max_speed_mps=260.0,
            max_g=5.0,
            max_bank_deg=60.0,
        )
        limits = compute_flight_limits(perf)

        v_cur = np.array([200.0, 0.0, 0.0])
        v_des = np.array([0.0, 200.0, 0.0])
        dt = 0.1

        v_out, dbg = limit_velocity_vector(v_cur, v_des, dt, limits)

        dir_cur = safe_unit(v_cur)
        dir_out = safe_unit(v_out)
        ang = angle_between(dir_cur, dir_out)

        self.assertLessEqual(ang, dbg["turn_max_angle_rad"] + 1e-6)
        self.assertAlmostEqual(np.linalg.norm(v_out), 200.0, places=6)

    def test_speed_accel_limit(self) -> None:
        perf = AircraftPerformance(min_speed_mps=0.0, max_accel_mps2=10.0, max_g=5.0, max_bank_deg=60.0)
        limits = compute_flight_limits(perf)
        v_cur = np.array([200.0, 0.0, 0.0])
        v_des = np.array([300.0, 0.0, 0.0])
        v_out, _ = limit_velocity_vector(v_cur, v_des, dt_s=1.0, limits=limits)
        self.assertLessEqual(np.linalg.norm(v_out), 210.0 + 1e-6)

    def test_climb_rate_limit(self) -> None:
        perf = AircraftPerformance(
            min_speed_mps=0.0,
            max_g=5.0,
            max_bank_deg=60.0,
            max_climb_rate_mps=10.0,
        )
        limits = compute_flight_limits(perf)
        v_cur = np.array([200.0, 0.0, 0.0])
        v_des = np.array([0.0, 150.0, 150.0])  # vz too high
        v_out, _ = limit_velocity_vector(v_cur, v_des, dt_s=0.1, limits=limits)
        self.assertLessEqual(float(v_out[2]), 10.0 + 1e-6)

    def test_descent_rate_limit(self) -> None:
        perf = AircraftPerformance(
            min_speed_mps=0.0,
            max_g=5.0,
            max_bank_deg=60.0,
            max_descent_rate_mps=25.0,
        )
        limits = compute_flight_limits(perf)
        v_cur = np.array([200.0, 0.0, 0.0])
        v_des = np.array([0.0, 150.0, -150.0])  # vz too negative
        v_out, _ = limit_velocity_vector(v_cur, v_des, dt_s=0.1, limits=limits)
        self.assertGreaterEqual(float(v_out[2]), -25.0 - 1e-6)


if __name__ == "__main__":
    unittest.main()
