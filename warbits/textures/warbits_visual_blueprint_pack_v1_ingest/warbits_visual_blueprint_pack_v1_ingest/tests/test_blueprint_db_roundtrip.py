import tempfile
import unittest
from pathlib import Path

from warbits.visual.blueprint_db import read_blueprints_jsonl, write_blueprints_jsonl
from warbits.visual.blueprint_schema import BlueprintRecord


class TestBlueprintDBRoundtrip(unittest.TestCase):
    def test_roundtrip(self):
        rec = BlueprintRecord(
            blueprint_id="vehicle:test",
            kind="vehicle",
            vertices_m=[(0.0, 0.0, 0.0), (1.0, 0.0, 0.0)],
            edges=[(0, 1)],
            tags=["vehicle"],
            meta={"license": "test"},
        )
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "bp.jsonl"
            write_blueprints_jsonl(p, [rec])
            out = read_blueprints_jsonl(p)
            self.assertEqual(len(out), 1)
            self.assertEqual(out[0].blueprint_id, rec.blueprint_id)
            self.assertEqual(out[0].edges, rec.edges)
            self.assertEqual(out[0].meta.get("license"), "test")


if __name__ == "__main__":
    unittest.main()
    unittest.main()
