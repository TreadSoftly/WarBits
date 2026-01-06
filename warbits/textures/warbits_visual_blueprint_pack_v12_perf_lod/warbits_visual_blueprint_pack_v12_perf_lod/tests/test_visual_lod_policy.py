import math

from warbits.visual.lod import CameraModel, LODPolicy, LODLevel, projected_radius_px


def test_projected_radius_px_basic():
    cam = CameraModel(vfov_deg=60.0, viewport_height_px=1080)
    px = projected_radius_px(radius_m=5.0, distance_m=100.0, cam=cam)
    assert px > 0
    # Rough sanity: radius 5m at 100m should not be huge
    assert px < 200


def test_lod_policy_ordering():
    policy = LODPolicy()

    # Very close & big -> HIGH
    assert policy.select(distance_m=200.0, projected_px=200.0) == LODLevel.HIGH

    # Medium size -> MED
    assert policy.select(distance_m=800.0, projected_px=40.0) == LODLevel.MED

    # Small -> LOW
    assert policy.select(distance_m=1500.0, projected_px=10.0) == LODLevel.LOW

    # Tiny / far -> ICON
    assert policy.select(distance_m=30000.0, projected_px=1.0) == LODLevel.ICON
