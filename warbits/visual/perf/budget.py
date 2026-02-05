from __future__ import annotations

from dataclasses import dataclass
from typing import List

from .stages import VisualStage
from .stats import VisualFrameTimings


@dataclass(frozen=True)
class VisualBudget:
    """Simple per-stage budgets in milliseconds.

    Budgets are **tripwires**, not sacred laws.

    - Use them to detect FPS regressions early.
    - Keep thresholds generous for CI runners.
    - Tighten thresholds on your own machine if you want.
    """

    terrain_ms: float = 4.0
    entities_ms: float = 4.0
    projectiles_ms: float = 3.0
    hud_ms: float = 1.0
    effects_ms: float = 2.0
    total_ms: float = 16.6  # ~60fps

    @staticmethod
    def from_target_fps(
        fps: float,
        *,
        terrain_frac: float = 0.25,
        entities_frac: float = 0.25,
        projectiles_frac: float = 0.20,
        hud_frac: float = 0.05,
        effects_frac: float = 0.10,
    ) -> "VisualBudget":
        frame_ms = 1000.0 / max(float(fps), 1.0)
        # Fractions do not need to sum to 1.0. Remaining slack is useful.
        return VisualBudget(
            terrain_ms=frame_ms * terrain_frac,
            entities_ms=frame_ms * entities_frac,
            projectiles_ms=frame_ms * projectiles_frac,
            hud_ms=frame_ms * hud_frac,
            effects_ms=frame_ms * effects_frac,
            total_ms=frame_ms,
        )

    def violations(self, timings: VisualFrameTimings) -> List[str]:
        ms = timings.ms_by_stage()
        out: List[str] = []

        def check(name: str, value_ms: float, budget_ms: float) -> None:
            if value_ms > budget_ms:
                out.append(f"{name} {value_ms:.3f}ms > budget {budget_ms:.3f}ms")

        check("terrain", ms[int(VisualStage.TERRAIN)], self.terrain_ms)
        check("entities", ms[int(VisualStage.ENTITIES)], self.entities_ms)
        check("projectiles", ms[int(VisualStage.PROJECTILES)], self.projectiles_ms)
        check("hud", ms[int(VisualStage.HUD)], self.hud_ms)
        check("effects", ms[int(VisualStage.EFFECTS)], self.effects_ms)
        check("total", timings.ms_total, self.total_ms)
        return out

    def assert_within_budget(self, timings: VisualFrameTimings) -> None:
        v = self.violations(timings)
        if v:
            msg = "\n".join(v)
            raise AssertionError(f"Visual budget violated:\n{msg}")


BudgetViolation = AssertionError
