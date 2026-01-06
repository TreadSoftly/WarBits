import unittest

import numpy as np

from warbits.simlib.flight.autopilot import L1Autopilot
from warbits.simlib.flight.envelope import compute_flight_limits
from warbits.simlib.flight.types import AircraftPerformance, Waypoint, WaypointNavigator


class TestSimlibFlightAutopilot(unittest.TestCase):
    def test_autopilot_turns_toward_waypoint(self) -> None:
        perf = AircraftPerformance(min_speed_mps=50.0, max_speed_mps=250.0, max_g=5.0, max_bank_deg=60.0)
        limits = compute_flight_limits(perf)

        ap = L1Autopilot(cruise_speed_mps=100.0)

        pos = np.array([0.0, 0.0, 0.0])
        vel = np.array([100.0, 0.0, 0.0])  # heading +X
        wp = Waypoint(np.array([0.0, 1000.0, 0.0]), acceptance_radius_m=50.0)  # to +Y

        cmd = ap.update(pos, vel, wp, limits, dt_s=0.1)
        d = cmd.target_direction_unit

        # Should have a positive Y component (turning toward waypoint).
        self.assertGreater(float(d[1]), 0.0)

    def test_autopilot_commands_climb(self) -> None:
        perf = AircraftPerformance(
            min_speed_mps=50.0,
            max_speed_mps=250.0,
            max_g=5.0,
            max_bank_deg=60.0,
            max_climb_rate_mps=15.0,
            max_descent_rate_mps=15.0,
        )
        limits = compute_flight_limits(perf)

        ap = L1Autopilot(cruise_speed_mps=120.0, altitude_gain=0.1)

        pos = np.array([0.0, 0.0, 0.0])
        vel = np.array([120.0, 0.0, 0.0])
        wp = Waypoint(np.array([1000.0, 0.0, 1000.0]))

        cmd = ap.update(pos, vel, wp, limits, dt_s=0.1)

        # Should command upward component (z > 0) and respect climb cap.
        self.assertGreater(float(cmd.target_direction_unit[2]), 0.0)
        v_des = cmd.target_direction_unit * cmd.target_speed_mps
        self.assertLessEqual(float(v_des[2]), 15.0 + 1e-6)

    def test_navigator_advances(self) -> None:
        perf = AircraftPerformance(min_speed_mps=50.0)
        limits = compute_flight_limits(perf)

        nav = WaypointNavigator(
            [
                Waypoint(np.array([0.0, 0.0, 0.0]), acceptance_radius_m=1.0),
                Waypoint(np.array([100.0, 0.0, 0.0]), acceptance_radius_m=1.0),
            ],
            loop=False,
        )

        ap = L1Autopilot(cruise_speed_mps=100.0)
        pos = np.array([0.0, 0.0, 0.0])
        vel = np.array([100.0, 0.0, 0.0])

        # First update should advance because we're at waypoint 0.
        cmd = ap.update_navigator(pos, vel, nav, limits, dt_s=0.1)
        self.assertEqual(nav.index, 1)
        self.assertIsNotNone(cmd)


if __name__ == "__main__":
    unittest.main()
