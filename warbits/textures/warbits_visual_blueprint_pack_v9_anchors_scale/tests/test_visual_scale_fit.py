import numpy as np

from warbits.visual.scale_fit import TargetDims, compute_uniform_scale, compute_nonuniform_scale, apply_scale


def test_uniform_scale_matches_length():
    # Local dims: length=10, span=4, height=2
    V = np.array([
        [0, -2, 0],
        [10, 2, 2],
    ], dtype=float)

    s = compute_uniform_scale(V, TargetDims(length_m=20.0))
    assert abs(s - 2.0) < 1e-6


def test_uniform_scale_uses_median_for_multiple_dims():
    # dims: (10, 4, 2). targets: (20, 8, 1) => ratios (2.0,2.0,0.5) median=2.0
    V = np.array([
        [0, -2, 0],
        [10, 2, 2],
    ], dtype=float)

    s = compute_uniform_scale(V, TargetDims(length_m=20.0, span_m=8.0, height_m=1.0))
    assert abs(s - 2.0) < 1e-6


def test_nonuniform_scale_per_axis():
    V = np.array([
        [0, -2, 0],
        [10, 2, 2],
    ], dtype=float)

    s = compute_nonuniform_scale(V, TargetDims(length_m=20.0, span_m=10.0, height_m=1.0))
    assert np.allclose(s, [2.0, 2.5, 0.5])

    V2 = apply_scale(V, s)
    dims = V2.max(axis=0) - V2.min(axis=0)
    assert np.allclose(dims, [20.0, 10.0, 1.0])
