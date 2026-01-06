import unittest
import numpy as np

from warbits.visual.hud import HudBuilder, HudTheme
from warbits.visual.hud.projector import PinholeProjector
from warbits.visual.hud.types import CameraInfo, HudContext, TargetTrack, WeaponInfo


class TestHudBuilder(unittest.TestCase):
    def test_build_drawlist_contains_crosshair(self):
        cam = CameraInfo(
            position_m=np.array([0.0, 0.0, 0.0]),
            forward=np.array([1.0, 0.0, 0.0]),
            up=np.array([0.0, 0.0, 1.0]),
            fov_y_deg=60.0,
            aspect=16 / 9,
        )
        ctx = HudContext(
            time_s=0.0,
            ownship_pos_m=np.array([0.0, 0.0, 1000.0]),
            ownship_vel_mps=np.array([200.0, 0.0, 0.0]),
            ownship_heading_deg=0.0,
            ownship_alt_m=1000.0,
            ownship_speed_mps=200.0,
            camera=cam,
            tracks=(),
            selected_track_id=None,
            weapon=WeaponInfo(weapon_family="gun", muzzle_speed_mps=900.0),
        )
        proj = PinholeProjector(cam)
        builder = HudBuilder(theme=HudTheme(pixel_snap=0))
        dl = builder.build(ctx, proj)
        self.assertGreater(len(dl), 4)  # text + crosshair

    def test_target_box_is_emitted_when_target_visible(self):
        cam = CameraInfo(
            position_m=np.array([0.0, 0.0, 0.0]),
            forward=np.array([1.0, 0.0, 0.0]),
            up=np.array([0.0, 0.0, 1.0]),
            fov_y_deg=60.0,
            aspect=1.0,
        )
        tgt = TargetTrack(track_id="T0", position_m=np.array([1000.0, 0.0, 0.0]), velocity_mps=np.zeros(3), hostile=True)
        ctx = HudContext(
            time_s=0.0,
            ownship_pos_m=np.array([0.0, 0.0, 0.0]),
            ownship_vel_mps=np.array([0.0, 0.0, 0.0]),
            ownship_heading_deg=0.0,
            ownship_alt_m=0.0,
            ownship_speed_mps=0.0,
            camera=cam,
            tracks=(tgt,),
            selected_track_id="T0",
            weapon=WeaponInfo(weapon_family="gun", muzzle_speed_mps=900.0),
        )
        proj = PinholeProjector(cam)
        builder = HudBuilder()
        dl = builder.build(ctx, proj)
        # Expect at least one HudBox primitive
        has_box = any(p.__class__.__name__ == "HudBox" for p in dl)
        self.assertTrue(has_box)


if __name__ == "__main__":
    unittest.main()
