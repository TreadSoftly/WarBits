import numpy as np

from warbits.visual.effects.trails import TrailParams, TrailRingBuffer


def test_trail_ring_buffer_emits_segments_and_alpha():
    params = TrailParams(4, 4)
    trail = TrailRingBuffer(params)

    # Two objects moving forward in x.
    ids = np.array([100, 200], dtype=np.int64)

    # Frame 0
    trail.ingest(ids, np.array([[0, 0, 0], [0, 1, 0]], dtype=np.float32))
    seg, a = trail.build_segments()
    assert seg.shape == (0, 2, 3)
    assert a.shape == (0,)

    # Frame 1
    trail.ingest(ids, np.array([[1, 0, 0], [1, 1, 0]], dtype=np.float32))
    seg, a = trail.build_segments()
    assert seg.shape[1:] == (2, 3)
    assert len(seg) == len(a)
    assert len(seg) == 2  # one segment per object (history_len=4 but only 2 points exist)

    # Segments should connect previous to current.
    seg_sorted = sorted(seg.tolist(), key=lambda s: (s[0][1], s[0][0]))
    assert np.allclose(seg_sorted[0][0], [0, 0, 0]) and np.allclose(seg_sorted[0][1], [1, 0, 0])
    assert np.allclose(seg_sorted[1][0], [0, 1, 0]) and np.allclose(seg_sorted[1][1], [1, 1, 0])

    # Alpha should be in 0..1
    assert np.all(a >= 0.0) and np.all(a <= 1.0)


def test_trail_ring_buffer_reset_clears():
    params = TrailParams(2, 3)
    trail = TrailRingBuffer(params)
    ids = np.array([1], dtype=np.int64)

    trail.ingest(ids, np.array([[0, 0, 0]], dtype=np.float32))
    trail.ingest(ids, np.array([[1, 0, 0]], dtype=np.float32))
    seg, _ = trail.build_segments()
    assert len(seg) == 1

    trail.reset()
    seg2, _ = trail.build_segments()
    assert len(seg2) == 0
