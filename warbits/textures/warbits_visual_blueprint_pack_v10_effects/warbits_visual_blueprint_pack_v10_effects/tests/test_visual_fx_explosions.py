import numpy as np

from warbits.visual.effects.explosions import ExplosionParams, ExplosionPool, make_unit_sphere_segments


def test_unit_sphere_segments_shape_and_bounds():
    seg = make_unit_sphere_segments(lat_steps=4, lon_steps=8)
    assert seg.ndim == 3 and seg.shape[1:] == (2, 3)
    # Should lie near unit sphere
    max_len = np.linalg.norm(seg.reshape(-1, 3), axis=1).max()
    assert max_len <= 1.0001


def test_explosion_pool_emits_and_expires():
    params = ExplosionParams(max_explosions=4, lifetime_frames=10, max_radius_m=50.0, lat_steps=3, lon_steps=6)
    pool = ExplosionPool(params)

    pool.spawn(center=(0, 0, 0), frame_idx=0, max_radius_m=20.0, lifetime_frames=5)
    seg0, a0 = pool.emit_segments(frame_idx=0)
    assert seg0.shape[1:] == (2, 3)
    assert len(seg0) == len(a0)
    assert len(seg0) > 0
    assert np.all(a0 >= 0.0) and np.all(a0 <= 1.0)

    # Past lifetime
    seg_dead, a_dead = pool.emit_segments(frame_idx=10)
    assert len(seg_dead) == 0
    assert len(a_dead) == 0
