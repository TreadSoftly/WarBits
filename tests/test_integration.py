import os
import unittest
import warnings

import matplotlib

os.environ["WARBITS_FULLSCREEN"] = "0"
matplotlib.use("Agg")

warnings.filterwarnings(
    "ignore",
    category=UserWarning,
    module=r"matplotlib\.animation",
)

class TestIntegration(unittest.TestCase):
    def test_ensure_animation(self) -> None:
        from warbits.scene import animation

        anim = animation.ensure_animation()
        self.assertIsNotNone(anim)
        import matplotlib.pyplot as plt

        fig = getattr(animation, "fig", None)
        if fig is not None:
            plt.close(fig)
