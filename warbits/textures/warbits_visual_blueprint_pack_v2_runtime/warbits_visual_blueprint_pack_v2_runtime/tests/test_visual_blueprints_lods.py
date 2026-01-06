import numpy as np

import pytest

try:
    import trimesh
except Exception:
    trimesh = None  # type: ignore

from warbits.visual.wireframe_extract import LODSpec, extract_lod_edge_sets


@pytest.mark.skipif(trimesh is None, reason="trimesh not installed")
def test_extract_lod_edges_monotonic():
    mesh = trimesh.creation.box(extents=(2.0, 1.0, 0.5))

    lods = (
        LODSpec(name="lod0", feature_angle_deg=5.0, max_edges=10000, sample_rate=1.0, include_boundary=True),
        LODSpec(name="lod1", feature_angle_deg=25.0, max_edges=5000, sample_rate=1.0, include_boundary=True),
        LODSpec(name="lod2", feature_angle_deg=55.0, max_edges=2000, sample_rate=1.0, include_boundary=True),
    )

    out = extract_lod_edge_sets(mesh, lods, rng_seed=1234)
    assert set(out.keys()) == {"lod0","lod1","lod2"}

    n0 = len(out["lod0"])
    n1 = len(out["lod1"])
    n2 = len(out["lod2"])

    assert n0 > 0
    assert n1 > 0
    assert n2 > 0
    assert n0 >= n1 >= n2
