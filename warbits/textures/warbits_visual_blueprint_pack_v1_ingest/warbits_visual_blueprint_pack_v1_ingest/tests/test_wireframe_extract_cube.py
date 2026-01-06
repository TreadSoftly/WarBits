import unittest
import numpy as np

from warbits.visual.mesh_io import MeshData
from warbits.visual.wireframe_extract import WireframeExtractParams, extract_wireframe_edges


def make_cube_mesh():
    # 8 vertices
    V = np.array([
        [0,0,0],
        [1,0,0],
        [1,1,0],
        [0,1,0],
        [0,0,1],
        [1,0,1],
        [1,1,1],
        [0,1,1],
    ], dtype=float)

    # 12 triangles (two per face)
    F = np.array([
        [0,1,2],[0,2,3],  # bottom
        [4,5,6],[4,6,7],  # top
        [0,1,5],[0,5,4],  # front
        [2,3,7],[2,7,6],  # back
        [1,2,6],[1,6,5],  # right
        [3,0,4],[3,4,7],  # left
    ], dtype=int)

    return MeshData(name="cube", vertices=V, faces=F)


class TestWireframeExtractCube(unittest.TestCase):
    def test_cube_edges(self):
        cube = make_cube_mesh()
        params = WireframeExtractParams(crease_angle_deg=10.0, max_edges=1000, min_edges=0, extra_rib_fraction=0.0)
        edges = extract_wireframe_edges(cube, params=params)
        # cube should yield exactly 12 feature edges (no diagonals, since diagonals are coplanar)
        self.assertEqual(len(edges), 12)
        # ensure unique
        self.assertEqual(len(edges), len(set(edges)))


if __name__ == "__main__":
    unittest.main()
