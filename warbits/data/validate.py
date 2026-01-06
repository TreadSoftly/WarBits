from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, TypeGuard

from .schema import FieldSpec, TableSchema, get_schema
from .store import DataStore

JsonDict = dict[str, object]


@dataclass(frozen=True)
class ValidationIssue:
    table: str
    row: int | None
    field: str
    message: str
    severity: str


@dataclass
class ValidationReport:
    issues: list[ValidationIssue]

    @property
    def error_count(self) -> int:
        return sum(1 for issue in self.issues if issue.severity == "error")

    @property
    def warning_count(self) -> int:
        return sum(1 for issue in self.issues if issue.severity == "warning")

    def extend(self, issues: Iterable[ValidationIssue]) -> None:
        self.issues.extend(issues)


def _is_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _is_dict(value: object) -> TypeGuard[JsonDict]:
    return isinstance(value, dict)


def _is_list(value: object) -> TypeGuard[list[object]]:
    return isinstance(value, list)


def _check_field(
    table: str,
    row: int | None,
    item: JsonDict,
    field: FieldSpec,
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if field.name not in item:
        if field.required:
            issues.append(
                ValidationIssue(
                    table=table,
                    row=row,
                    field=field.name,
                    message="missing required field",
                    severity="error",
                )
            )
        return issues
    value = item.get(field.name)
    if value is None and field.allow_none:
        return issues
    if value is None and field.required:
        issues.append(
            ValidationIssue(
                table=table,
                row=row,
                field=field.name,
                message="required field is null",
                severity="error",
            )
        )
        return issues
    if value is None:
        return issues
    if field.types:
        if field.types == (int, float) and not _is_number(value):
            issues.append(
                ValidationIssue(
                    table=table,
                    row=row,
                    field=field.name,
                    message=f"expected numeric, got {type(value).__name__}",
                    severity="warning",
                )
            )
            return issues
        if not isinstance(value, field.types):
            issues.append(
                ValidationIssue(
                    table=table,
                    row=row,
                    field=field.name,
                    message=f"expected {field.types}, got {type(value).__name__}",
                    severity="warning",
                )
            )
    return issues


def _validate_list(schema: TableSchema, data: object) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if not _is_list(data):
        issues.append(
            ValidationIssue(
                table=schema.name,
                row=None,
                field="__root__",
                message="expected a list",
                severity="error",
            )
        )
        return issues
    for idx, item in enumerate(data):
        if not _is_dict(item):
            issues.append(
                ValidationIssue(
                    table=schema.name,
                    row=idx,
                    field="__root__",
                    message="expected object",
                    severity="error",
                )
            )
            continue
        item_dict = item
        for spec in schema.required_fields:
            issues.extend(_check_field(schema.name, idx, item_dict, spec))
        for spec in schema.optional_fields:
            issues.extend(_check_field(schema.name, idx, item_dict, spec))
    return issues


def _validate_dict(schema: TableSchema, data: object) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if not _is_dict(data):
        issues.append(
            ValidationIssue(
                table=schema.name,
                row=None,
                field="__root__",
                message="expected an object",
                severity="error",
            )
        )
        return issues
    item_dict = data
    for spec in schema.required_fields:
        issues.extend(_check_field(schema.name, None, item_dict, spec))
    for spec in schema.optional_fields:
        issues.extend(_check_field(schema.name, None, item_dict, spec))
    return issues


def validate_table(name: str, data: object) -> ValidationReport:
    schema = get_schema(name)
    issues: list[ValidationIssue]
    if schema.kind == "list":
        issues = _validate_list(schema, data)
    else:
        issues = _validate_dict(schema, data)
    return ValidationReport(issues)


def _validate_cross_links(store: DataStore) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    weapon_index: set[str] = set()
    for weapon in store.weapons:
        weapon_id = weapon.get("id")
        if isinstance(weapon_id, str):
            weapon_index.add(weapon_id)
    warhead_index: set[str] = set()
    for warhead in store.warheads:
        warhead_id = warhead.get("id")
        if isinstance(warhead_id, str):
            warhead_index.add(warhead_id)

    for idx, weapon in enumerate(store.weapons):
        warhead_id = weapon.get("warhead_id")
        if isinstance(warhead_id, str) and warhead_id not in warhead_index:
            issues.append(
                ValidationIssue(
                    table="weapons",
                    row=idx,
                    field="warhead_id",
                    message=f"unknown warhead_id {warhead_id!r}",
                    severity="error",
                )
            )

    for idx, warhead in enumerate(store.warheads):
        weapon_id = warhead.get("weapon_id")
        if isinstance(weapon_id, str) and weapon_id not in weapon_index:
            issues.append(
                ValidationIssue(
                    table="warheads",
                    row=idx,
                    field="weapon_id",
                    message=f"unknown weapon_id {weapon_id!r}",
                    severity="error",
                )
            )
    return issues


def _validate_summary_counts(store: DataStore) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    summary = store.summary
    counts = summary.get("counts")
    if not _is_dict(counts):
        return issues
    counts_dict = counts
    expected = {
        "vehicles": len(store.vehicles),
        "weapons": len(store.weapons),
        "warheads": len(store.warheads),
        "sensors": len(store.sensors),
        "terrain": len(store.terrain),
    }
    for key, value in expected.items():
        actual = counts_dict.get(key)
        if actual != value:
            issues.append(
                ValidationIssue(
                    table="summary",
                    row=None,
                    field=f"counts.{key}",
                    message=f"count mismatch: expected {value}, got {actual!r}",
                    severity="warning",
                )
            )
    return issues


def validate_all(store: DataStore) -> ValidationReport:
    issues: list[ValidationIssue] = []
    report = ValidationReport(issues)
    for name in store.list_tables():
        data = store.load_table(name)
        report.extend(validate_table(name, data).issues)
    report.extend(_validate_cross_links(store))
    report.extend(_validate_summary_counts(store))
    return report


__all__ = [
    "ValidationIssue",
    "ValidationReport",
    "validate_table",
    "validate_all",
]
