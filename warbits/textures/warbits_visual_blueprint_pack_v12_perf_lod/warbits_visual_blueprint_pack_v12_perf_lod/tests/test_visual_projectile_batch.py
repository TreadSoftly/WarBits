import numpy as np

from warbits.visual.batch import ProjectileSegmentBatch


def test_projectile_segment_batch_shapes():
    b = ProjectileSegmentBatch(max_segments=8)

    prev = np.zeros((5, 3), dtype=np.float32)
    curr = np.ones((5, 3), dtype=np.float32)

    seg = b.update(prev, curr)
    assert seg.shape == (5, 2, 3)
    # Ensure first segment is prev->curr
    assert np.allclose(seg[0, 0], prev[0])
    assert np.allclose(seg[0, 1], curr[0])


def test_projectile_batch_clamps_to_max():
    b = ProjectileSegmentBatch(max_segments=2)
    prev = np.zeros((5, 3), dtype=np.float32)
    curr = np.ones((5, 3), dtype=np.float32)
    seg = b.update(prev, curr)
    assert seg.shape == (2, 2, 3)
