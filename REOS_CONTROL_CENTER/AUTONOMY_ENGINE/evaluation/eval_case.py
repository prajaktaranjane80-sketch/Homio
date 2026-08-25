"""Evaluation case primitives for AUTONOMY_ENGINE V6."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping


@dataclass(frozen=True)
class EvaluationCase:
    """A deterministic, machine-readable evaluation case."""

    case_id: str
    name: str
    description: str
    category: str
    input_data: Mapping[str, Any]
    expected: Mapping[str, Any]
    tags: tuple[str, ...] = field(default_factory=tuple)
    enabled: bool = True

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-compatible representation."""
        return {
            "case_id": self.case_id,
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "input_data": dict(self.input_data),
            "expected": dict(self.expected),
            "tags": list(self.tags),
            "enabled": self.enabled,
        }


@dataclass(frozen=True)
class EvaluationResult:
    """Result of evaluating one case."""

    case_id: str
    passed: bool
    actual: Mapping[str, Any]
    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-compatible representation."""
        return {
            "case_id": self.case_id,
            "passed": self.passed,
            "actual": dict(self.actual),
            "reason": self.reason,
        }


def evaluate_mapping(
    case: EvaluationCase,
    actual: Mapping[str, Any],
) -> EvaluationResult:
    """Evaluate expected key/value pairs against an actual result.

    The evaluator intentionally performs only deterministic comparison.
    Policy, authorization, governance, and execution remain outside this
    module.
    """
    if not case.enabled:
        return EvaluationResult(
            case_id=case.case_id,
            passed=False,
            actual=dict(actual),
            reason="Evaluation case is disabled.",
        )

    mismatches: list[str] = []

    for key, expected_value in case.expected.items():
        if actual.get(key) != expected_value:
            mismatches.append(
                f"{key}: expected {expected_value!r}, "
                f"got {actual.get(key)!r}"
            )

    if mismatches:
        return EvaluationResult(
            case_id=case.case_id,
            passed=False,
            actual=dict(actual),
            reason="; ".join(mismatches),
        )

    return EvaluationResult(
        case_id=case.case_id,
        passed=True,
        actual=dict(actual),
        reason="All expected values matched.",
    )