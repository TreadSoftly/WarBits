import tempfile
import unittest

from warbits.core.event_log import Event, read_jsonl, write_jsonl
from warbits.core.events import DebugEvent, ExplosionEvent, ImpactEvent, ParachuteEvent


class TestEventsRoundtrip(unittest.TestCase):
    def test_roundtrip_jsonl(self) -> None:
        events: list[Event] = [
            ImpactEvent(
                frame=10,
                x=1.0,
                y=2.0,
                z=3.0,
                target="terrain",
                weapon="bomb",
                metadata={"note": "test"},
            ),
            ExplosionEvent(
                frame=11,
                x=4.0,
                y=5.0,
                z=6.0,
                scale=1.5,
                style="mushroom",
            ),
            ParachuteEvent(
                frame=12,
                x=7.0,
                y=8.0,
                z=9.0,
                vx=1.0,
                vy=2.0,
                vz=3.0,
            ),
            DebugEvent(
                frame=13,
                kind="physics",
                payload={"detail": "ok"},
            ),
        ]
        with tempfile.TemporaryDirectory() as tmpdir:
            path = f"{tmpdir}/events.jsonl"
            write_jsonl(path, events)
            loaded = read_jsonl(path)
        self.assertEqual(loaded, events)

    def test_impact_mapping_access(self) -> None:
        event = ImpactEvent(
            frame=1,
            x=0.0,
            y=0.0,
            z=0.0,
            target="aircraft",
            weapon="rocket",
            metadata={"extra": 123},
        )
        self.assertEqual(event["weapon"], "rocket")
        self.assertEqual(event.get("target"), "aircraft")
        self.assertEqual(event["extra"], 123)
        with self.assertRaises(KeyError):
            _ = event["missing"]
