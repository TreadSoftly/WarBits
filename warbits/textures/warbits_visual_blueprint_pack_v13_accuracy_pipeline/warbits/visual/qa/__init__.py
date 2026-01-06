"""Visual QA utilities for the Visual Blueprint system (v13 consolidation).

This package is intentionally renderer-agnostic.

Use it via the CLI:
    python -m warbits.visual.tools.pipeline validate

Or call validators directly.
"""

from .schema_validate import SchemaValidationResult, validate_blueprints_jsonl
from .anchors_validate import AnchorsValidationResult, validate_anchors_jsonl
from .scale_validate import ScaleValidationResult, TargetDims, validate_blueprint_scale, validate_blueprints_scale
from .budget_validate import BudgetSpec, BudgetValidationResult, validate_blueprints_budgets
from .coverage import CoverageReport, build_coverage_report
from .provenance import ProvenanceRecord, ProvenanceReport, check_provenance, load_provenance_records
from .perf_scenes import PerfSceneResult, run_perf_regression

__all__ = [
    "SchemaValidationResult",
    "validate_blueprints_jsonl",
    "AnchorsValidationResult",
    "validate_anchors_jsonl",
    "ScaleValidationResult",
    "TargetDims",
    "validate_blueprint_scale",
    "validate_blueprints_scale",
    "BudgetSpec",
    "BudgetValidationResult",
    "validate_blueprints_budgets",
    "CoverageReport",
    "build_coverage_report",
    "ProvenanceRecord",
    "ProvenanceReport",
    "load_provenance_records",
    "check_provenance",
    "PerfSceneResult",
    "run_perf_regression",
]
