import unittest

from warbits.logic.flight_paths import build_flight_plan

_PHASES = ["Approach", "Strafe", "Bombing", "Escape", "Dogfight"]


class TestFlightPathsValidation(unittest.TestCase):
    def test_missing_phases_use_defaults(self) -> None:
        phases = {
            "Approach": ("blue", 5),
            "Dogfight": ("purple", 6),
        }
        flight_x, flight_y, flight_z, slices = build_flight_plan(phases)
        self.assertEqual(len(flight_x), len(flight_y))
        self.assertEqual(len(flight_x), len(flight_z))
        for name in _PHASES:
            self.assertIn(name, slices)
            start, end = slices[name]
            self.assertGreaterEqual(end - start, 2)
        self.assertEqual(slices["Victory2"][1], len(flight_x))

    def test_short_phase_lengths_are_clamped(self) -> None:
        phases = {
            "Approach": ("blue", 1),
            "Strafe": ("orange", 0),
            "Bombing": ("red", -5),
            "Escape": ("green", 1),
            "Dogfight": ("purple", 1),
        }
        _, _, _, slices = build_flight_plan(phases)
        for name in _PHASES:
            start, end = slices[name]
            self.assertGreaterEqual(end - start, 2)
