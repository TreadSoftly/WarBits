import numpy as np

from warbits.visual.effects.bursts import BurstParams, BurstPool, make_unit_starburst_segments


def test_starburst_segments_in_plane():
    seg = make_unit_starburst_segments(rays=16)
    assert seg.shape == (16, 2, 3)
    assert np.allclose(seg[:, 0, :], 0.0)
    assert np.allclose(seg[:, :, 2], 0.0)  # Z=0 plane


def test_burst_pool_emits_and_expires():
    params = BurstParams(max_bursts=4, lifetime_frames=10, rays=8, radius_m=5.0)
    pool = BurstPool(params)

    pool.spawn(center_xyz_m=np.array([1.0, 2.0, 3.0], dtype=np.float32), frame_idx=0)
    seg, a = pool.build_segments(frame_idx=0)
    assert seg.shape[1:] == (2, 3)
    assert len(seg) == len(a)
    assert len(seg) > 0

    # It should be centered near (1,2,3)
    mid = seg.mean(axis=(0, 1))
    assert np.allclose(mid, np.array([1, 2, 3]), atol=1.0)

    seg_dead, a_dead = pool.build_segments(frame_idx=20)
    assert len(seg_dead) == 0
    assert len(a_dead) == 0
    assert len(a_dead) == 0
