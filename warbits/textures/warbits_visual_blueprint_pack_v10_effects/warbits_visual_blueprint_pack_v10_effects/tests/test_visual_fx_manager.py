import numpy as np

from warbits.visual.effects.config import FxConfig
from warbits.visual.effects.manager import FxManager


def test_fx_manager_builds_layers():
    cfg = FxConfig(
        tracer_max_objects=8,
        contrail_max_objects=4,
        max_tracer_segments=64,
        max_contrail_segments=64,
        max_explosions=4,
        max_impacts=4,
    )

    fx = FxManager(cfg)

    # Simulate a moving bullet in 3 frames
    bullet_id = np.array([123], dtype=np.int64)
    for frame in range(3):
        p = np.array([[float(frame), 0.0, 0.0]], dtype=np.float32)
        fx.update_trail("tracers", bullet_id, p, frame_idx=frame)

    fx.spawn_explosion(np.array([0.0, 0.0, 0.0], dtype=np.float32), frame_idx=2)
    fx.spawn_impact_burst(
        np.array([1.0, 0.0, 0.0], dtype=np.float32), normal_xyz=np.array([0.0, 0.0, 1.0], dtype=np.float32), frame_idx=2
    )

    frame = fx.build_frame(frame_idx=2)
    assert "tracers" in frame.layers
    assert "explosions" in frame.layers
    assert "impacts" in frame.layers

    assert frame.layers["tracers"].segments.shape[1:] == (2, 3)
    assert frame.layers["explosions"].segments.shape[1:] == (2, 3)
    assert frame.layers["impacts"].segments.shape[1:] == (2, 3)


def test_fx_manager_ingest_event_dicts():
    fx = FxManager(FxConfig())

    events: list[dict[str, object]] = [
        {"type": "explosion", "pos": (0, 0, 0), "radius": 10.0},
        {"type": "impact", "pos": (1, 2, 3), "normal": (0, 0, 1)},
    ]

    fx.ingest_event_dicts(events, frame_idx=0)
    frame = fx.build_frame(frame_idx=0)
    assert len(frame.layers["explosions"].segments) > 0
    assert len(frame.layers["impacts"].segments) > 0
