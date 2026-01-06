import tempfile
from pathlib import Path
import unittest

from warbits.visual.mesh_io import read_obj_objects


MULTI_OBJ = """# multi-object test
o CubeA
v 0 0 0
v 1 0 0
v 1 1 0
v 0 1 0
v 0 0 1
v 1 0 1
v 1 1 1
v 0 1 1
f 1 2 3 4
f 5 6 7 8

o CubeB
v 2 0 0
v 3 0 0
v 3 1 0
v 2 1 0
v 2 0 1
v 3 0 1
v 3 1 1
v 2 1 1
f 9 10 11 12
f 13 14 15 16
"""


class TestObjMultiLoader(unittest.TestCase):
    def test_splits_objects(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "two.obj"
            p.write_text(MULTI_OBJ, encoding="utf-8")
            meshes = read_obj_objects(p)
            self.assertIn("CubeA", meshes)
            self.assertIn("CubeB", meshes)
            self.assertGreaterEqual(len(meshes["CubeA"].faces), 2)
            self.assertGreaterEqual(len(meshes["CubeB"].faces), 2)


if __name__ == "__main__":
    unittest.main()
