import os
import tempfile

from warbits.vislib.mesh.obj import load_obj
from warbits.vislib.mesh.wireframe import edges_from_faces

CUBE_OBJ = """    v 0 0 0
v 1 0 0
v 1 1 0
v 0 1 0
v 0 0 1
v 1 0 1
v 1 1 1
v 0 1 1
f 1 2 3 4
f 5 6 7 8
f 1 2 6 5
f 2 3 7 6
f 3 4 8 7
f 4 1 5 8
"""

def test_load_obj_and_edges():
    with tempfile.TemporaryDirectory() as td:
        p = os.path.join(td, "cube.obj")
        with open(p, "w", encoding="utf-8") as f:
            f.write(CUBE_OBJ)
        mesh = load_obj(p, triangulate=True)
        assert len(mesh.vertices) == 8
        # faces triangulated: 6 quads -> 12 tris
        assert len(mesh.faces) == 12
        edges = edges_from_faces(mesh.faces)
        # a cube has 12 unique edges (but triangulation adds diagonals;
        # edges_from_faces includes those diagonals too, so it's > 12)
        assert len(edges) > 12
