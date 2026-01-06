# Panda3D Terrain + Camera + HUD primitives

This pack adds three high-value building blocks for the Panda3D rendering path:

- Terrain: a dark heightfield surface + optional sparse wire grid overlay
- Camera: a stable chase camera controller (consistent across uncapped FPS)
- HUD: minimal neon-green text blocks + center reticle

These are intentionally *primitive* pieces — they are designed to be composed into
your real game loop later (v10 on the roadmap).

---

## Install requirements

You only need Panda3D when you actually run the Panda3D visual path.

- `pip install panda3d`

The module files are safe to import without Panda3D installed; they only require
Panda3D at runtime when you construct nodes.

---

## Quick demo scaffold (copy into a scratch file)

```python
import numpy as np

from direct.showbase.ShowBase import ShowBase

from warbits.visual.panda3d.blueprint_layer import P3DBlueprintLayer
from warbits.visual.panda3d.camera import ChaseCameraController
from warbits.visual.panda3d.hud import BasicHUD
from warbits.visual.panda3d.terrain import HeightfieldSpec, P3DTerrain


class App(ShowBase):
    def __init__(self):
        super().__init__()

        # --- terrain ---
        n = 128
        xs = np.linspace(-500, 500, n, dtype=np.float32)
        ys = np.linspace(-500, 500, n, dtype=np.float32)
        X, Y = np.meshgrid(xs, ys)
        Z = 10.0 * np.sin(X / 90.0) * np.cos(Y / 110.0)  # cheap hills

        spec = HeightfieldSpec(Z, x0=float(xs[0]), y0=float(ys[0]), dx=float(xs[1]-xs[0]), dy=float(ys[1]-ys[0]))
        self.terrain = P3DTerrain(self.render, spec)

        # --- blueprint layer ---
        self.bp = P3DBlueprintLayer(self.render)

        # Spawn a single aircraft blueprint (use your real vehicle ids later).
        self.air = self.bp.spawn(
            blueprint_id="proc_air_fighter_generic",
            pose={"pos": (0.0, 0.0, 60.0), "hpr": (0.0, 0.0, 0.0), "scale": 1.0},
            style_id="default",
        )

        # --- camera + HUD ---
        self.cam_ctrl = ChaseCameraController(self.camera)
        self.hud = BasicHUD(self)

        self.t = 0.0
        self.taskMgr.add(self.update, "update")

    def update(self, task):
        dt = globalClock.getDt()
        self.t += dt

        # Fake “aircraft” motion (circle)
        x = 200.0 * np.cos(self.t * 0.25)
        y = 200.0 * np.sin(self.t * 0.25)
        z = 70.0 + 10.0 * np.sin(self.t * 0.8)

        vx = -200.0 * 0.25 * np.sin(self.t * 0.25)
        vy =  200.0 * 0.25 * np.cos(self.t * 0.25)
        vz =  10.0 * 0.8 * np.cos(self.t * 0.8)

        self.bp.set_pose(self.air, pos=(float(x), float(y), float(z)), hpr=(float(self.t * 20.0), 0.0, 0.0))

        self.cam_ctrl.update(dt, np.array([x, y, z], dtype=np.float32), np.array([vx, vy, vz], dtype=np.float32))
        self.hud.update_basic(speed_mps=float((vx*vx + vy*vy + vz*vz) ** 0.5), altitude_m=float(z), heading_deg=float((self.t * 20.0) % 360.0), fps=1.0/max(dt, 1e-6))

        return task.cont


App().run()
```

---

## Performance notes (the stuff that keeps FPS “stupid high”)

- Terrain mesh is **UHStatic** and built once. Keep heightfield sizes reasonable (128–256).
- Terrain wire grid uses a **stride**. Bigger stride = fewer segments = faster.
- Vehicle wireframes are batched by `P3DBlueprintLayer` into a **single dynamic line batch**.
- Avoid creating/destroying NodePaths every frame. Update poses instead.

---

## Where this goes next

- v7: starter blueprint dataset and tooling
- v8–v9: pixel look, effects, and label systems
- v10: full integration into the WarBits simulation loop (entity-to-visual binding)
