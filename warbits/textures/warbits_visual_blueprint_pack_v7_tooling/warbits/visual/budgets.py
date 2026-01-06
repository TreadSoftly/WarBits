"""warbits.visual.budgets

FPS-first complexity budgets for wireframe / hologram blueprints.

This is a guardrail system:
- stops accidental 10k-edge monsters
- keeps LOD cheap at distance
- preserves uncapped-FPS ambitions

Budgets are conservative defaults.
Tune them after profiling on your target hardware.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Mapping, Optional, Sequence, Tuple

from .blueprint_schema import Blueprint, Edge


@dataclass(frozen=True)
class BlueprintBudget:
    """Upper bounds for blueprint complexity."""

    max_vertices: int
    max_edges: int

    # Soft cap: too many LOD layers usually means you are storing noise.
    max_lod_levels: int = 4

    notes: str = ""


@dataclass(frozen=True)
class BudgetCheckResult:
    ok: bool
    reasons: Tuple[str, ...] = ()

    @staticmethod
    def pass_() -> "BudgetCheckResult":
        return BudgetCheckResult(ok=True, reasons=())

    @staticmethod
    def fail(*reasons: str) -> "BudgetCheckResult":
        return BudgetCheckResult(ok=False, reasons=tuple(reasons))


# -----------------------------------------------------------------------------
# LOD aliasing
# -----------------------------------------------------------------------------

LOD_ALIASES = {
    "near": "lod0",
    "mid": "lod1",
    "far": "lod2",
}


def normalize_lod_name(lod: str) -> str:
    lod = (lod or "").strip().lower()
    return LOD_ALIASES.get(lod, lod or "lod0")


# -----------------------------------------------------------------------------
# Default budgets
# -----------------------------------------------------------------------------
#
# Philosophy: these are "wireframe overlay" budgets, not CAD wireframe budgets.
# A hologram/wireframe replay look should be:
#   silhouette + a few ribs + a few cues
# not:
#   every triangle edge
#

DEFAULT_BUDGETS: Dict[str, Dict[str, BlueprintBudget]] = {
    "vehicle": {
        "lod0": BlueprintBudget(max_vertices=600, max_edges=900, notes="close/high detail"),
        "lod1": BlueprintBudget(max_vertices=220, max_edges=320, notes="mid distance"),
        "lod2": BlueprintBudget(max_vertices=80, max_edges=120, notes="far silhouette"),
        "lod3": BlueprintBudget(max_vertices=45, max_edges=70, notes="ultra-far fallback"),
    },
    "weapon": {
        "lod0": BlueprintBudget(max_vertices=160, max_edges=240),
        "lod1": BlueprintBudget(max_vertices=80, max_edges=120),
        "lod2": BlueprintBudget(max_vertices=30, max_edges=45),
        "lod3": BlueprintBudget(max_vertices=18, max_edges=26),
    },
    "sensor": {
        "lod0": BlueprintBudget(max_vertices=100, max_edges=140),
        "lod1": BlueprintBudget(max_vertices=60, max_edges=90),
        "lod2": BlueprintBudget(max_vertices=25, max_edges=40),
        "lod3": BlueprintBudget(max_vertices=16, max_edges=24),
    },
    "effect": {
        "lod0": BlueprintBudget(max_vertices=220, max_edges=320),
        "lod1": BlueprintBudget(max_vertices=120, max_edges=180),
        "lod2": BlueprintBudget(max_vertices=50, max_edges=90),
        "lod3": BlueprintBudget(max_vertices=30, max_edges=60),
    },
}


def infer_budget_kind(bp: Blueprint) -> str:
    """Return which DEFAULT_BUDGETS key to use for this blueprint."""
    if bp.kind in DEFAULT_BUDGETS:
        return bp.kind
    return "vehicle"


def select_edges_for_lod(bp: Blueprint, lod: str) -> Sequence[Edge]:
    lod = normalize_lod_name(lod)
    if bp.lod_edges and lod in bp.lod_edges:
        return bp.lod_edges[lod]
    return bp.edges


def check_budget(
    bp: Blueprint,
    lod: str,
    budgets: Mapping[str, Mapping[str, BlueprintBudget]] = DEFAULT_BUDGETS,
) -> BudgetCheckResult:
    lod = normalize_lod_name(lod)

    kind = infer_budget_kind(bp)
    kind_budgets = budgets.get(kind) or budgets["vehicle"]
    budget = kind_budgets.get(lod) or kind_budgets.get("lod0")  # default to lod0 if unknown

    reasons = []

    edges = select_edges_for_lod(bp, lod)
    v_count = len(bp.vertices_m)
    e_count = len(edges)

    if v_count > budget.max_vertices:
        reasons.append(f"vertices {v_count} > budget {budget.max_vertices} ({kind}/{lod})")

    if e_count > budget.max_edges:
        reasons.append(f"edges {e_count} > budget {budget.max_edges} ({kind}/{lod})")

    if bp.lod_edges and len(bp.lod_edges) > budget.max_lod_levels:
        reasons.append(f"lod_levels {len(bp.lod_edges)} > budget {budget.max_lod_levels} ({kind}/{lod})")

    return BudgetCheckResult.pass_() if not reasons else BudgetCheckResult.fail(*reasons)
