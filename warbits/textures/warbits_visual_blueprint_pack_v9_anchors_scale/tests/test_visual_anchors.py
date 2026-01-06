import numpy as np

from warbits.visual.anchors import compute_default_anchors, merge_anchor_maps


def test_default_anchors_within_bounds_aircraftish():
    # Simple box: x in [0, 10], y in [-5, 5], z in [0, 2]
    V = np.array([
        [0, -5, 0],
        [10, 5, 2],
        [10, -5, 2],
        [0, 5, 0],
    ], dtype=float)

    anchors = compute_default_anchors(
        blueprint_id="vehicle.aircraft.testjet",
        vertices_m=V,
        kind_hint="vehicle.aircraft",
        meta_kind="vehicle",
    )

    vmin = V.min(axis=0)
    vmax = V.max(axis=0)

    # Must include some core anchors
    for k in ["center", "nose", "tail", "left_wing_tip", "right_wing_tip", "pylon_left_1", "pylon_right_1"]:
        assert k in anchors

    # All anchors should lie within (or on) bbox for our default generator
    for k, p in anchors.items():
        assert p.shape == (3,)
        assert np.all(p >= vmin - 1e-6), f"{k} below min"
        assert np.all(p <= vmax + 1e-6), f"{k} above max"


def test_merge_anchor_maps_override_wins():
    base = {"mount": np.array([1.0, 2.0, 3.0])}
    override = {"mount": np.array([9.0, 8.0, 7.0]), "extra": np.array([0.0, 0.0, 0.0])}

    merged = merge_anchor_maps(base, override)

    assert np.allclose(merged["mount"], [9.0, 8.0, 7.0])
    assert np.allclose(merged["extra"], [0.0, 0.0, 0.0])
