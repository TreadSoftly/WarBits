import os
import unittest

os.environ.setdefault("MPLBACKEND", "Agg")

from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
from mpl_toolkits.mplot3d import Axes3D  # type: ignore  # noqa: F401

from warbits.logic.state import RUNTIME
from warbits.config import settings as _cfg
from warbits.physics import bombs


class TestBombRelease(unittest.TestCase):
    def setUp(self) -> None:
        bombs.reset()
        RUNTIME.active_bombs.clear()

    def tearDown(self) -> None:
        bombs.reset()
        RUNTIME.active_bombs.clear()

    def test_release_uses_plane_velocity(self) -> None:
        fig = Figure()
        FigureCanvas(fig)
        ax = fig.add_subplot(111, projection="3d")

        pos = (0.0, 0.0, 1000.0)
        vel = (200.0, 0.0, 0.0)

        bombs.schedule_release(0)
        dt = 1.0
        bombs.step(
            0,
            pos,
            vel,
            ax,
            dt=dt,
            drag_coefficient=0.0,
            max_time=2.0,
        )

        paths = RUNTIME.active_bombs.paths
        lengths = RUNTIME.active_bombs.lengths
        self.assertGreaterEqual(paths.shape[0], 1)
        path_x = paths[0, 0, : lengths[0]]
        self.assertGreaterEqual(path_x.size, 2)
        sim_dt = max(float(_cfg.SIM_DT_MS) / 1000.0, 1e-6)
        expected = vel[0] * sim_dt
        self.assertAlmostEqual(float(path_x[1]), expected, delta=1e-3)

        fig.clear()
