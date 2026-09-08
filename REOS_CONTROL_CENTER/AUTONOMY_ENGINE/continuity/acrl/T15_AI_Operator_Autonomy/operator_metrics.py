"""
ACRL T15 — Operator Metrics.

Read-only metrics derived from immutable T15 operator reports.

This module never:
    - mutates authoritative state,
    - executes operations,
    - authorizes execution,
    - changes controller state.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


class OperatorMetricsError(ValueError):
    """Raised when T15 metrics input is invalid."""


@dataclass(frozen=True)
class OperatorMetrics:
    """Immutable T15 outcome metrics."""

    proposals: int = 0
    blocked: int = 0
    fail_closed: int = 0
    execution_authorized: int = 0
    state_mutations: int = 0

    def __post_init__(self) -> None:
        fields = (
            "proposals",
            "blocked",
            "fail_closed",
            "execution_authorized",
            "state_mutations",
        )

        for field_name in fields:
            value = getattr(self, field_name)

            if not isinstance(value, int):
                raise OperatorMetricsError(
                    f"{field_name} must be an integer."
                )

            if isinstance(value, bool):
                raise OperatorMetricsError(
                    f"{field_name} must be an integer."
                )

            if value < 0:
                raise OperatorMetricsError(
                    f"{field_name} cannot be negative."
                )

    def to_dict(self) -> dict[str, int]:
        """Return serializable metrics."""

        return {
            "proposals": self.proposals,
            "blocked": self.blocked,
            "fail_closed": self.fail_closed,
            "execution_authorized": self.execution_authorized,
            "state_mutations": self.state_mutations,
        }


class OperatorMetricsEngine:
    """Deterministic T15 metrics derivation engine."""

    VERSION = "T15-METRICS-1.0"

    @classmethod
    def from_report(
        cls,
        report: Any,
    ) -> OperatorMetrics:
        """Derive metrics from an immutable T15 report."""

        if report is None:
            raise OperatorMetricsError(
                "T15 report cannot be None."
            )

        required_fields = (
            "decision",
            "execution_authorized",
            "state_mutated",
        )

        for field_name in required_fields:
            if not hasattr(report, field_name):
                raise OperatorMetricsError(
                    f"Report is missing field: {field_name}"
                )

        decision = getattr(report, "decision")

        decision_value = getattr(
            decision,
            "value",
            decision,
        )

        if not isinstance(decision_value, str):
            raise OperatorMetricsError(
                "Report decision must be string-compatible."
            )

        execution_authorized = getattr(
            report,
            "execution_authorized",
        )

        state_mutated = getattr(
            report,
            "state_mutated",
        )

        if not isinstance(execution_authorized, bool):
            raise OperatorMetricsError(
                "execution_authorized must be boolean."
            )

        if not isinstance(state_mutated, bool):
            raise OperatorMetricsError(
                "state_mutated must be boolean."
            )

        # T15 invariant: execution authorization must never occur.
        if execution_authorized:
            raise OperatorMetricsError(
                "T15 metrics detected execution authorization."
            )

        # T15 invariant: state mutation must never occur.
        if state_mutated:
            raise OperatorMetricsError(
                "T15 metrics detected state mutation."
            )

        return OperatorMetrics(
            proposals=(
                1
                if decision_value == "PROPOSE"
                else 0
            ),
            blocked=(
                1
                if decision_value == "BLOCK"
                else 0
            ),
            fail_closed=(
                1
                if decision_value == "FAIL_CLOSED"
                else 0
            ),
            execution_authorized=0,
            state_mutations=0,
        )

    @classmethod
    def combine(
        cls,
        *metrics: OperatorMetrics,
    ) -> OperatorMetrics:
        """Combine immutable metric snapshots."""

        for item in metrics:
            if not isinstance(item, OperatorMetrics):
                raise OperatorMetricsError(
                    "All metric inputs must be OperatorMetrics."
                )

        return OperatorMetrics(
            proposals=sum(item.proposals for item in metrics),
            blocked=sum(item.blocked for item in metrics),
            fail_closed=sum(
                item.fail_closed
                for item in metrics
            ),
            execution_authorized=sum(
                item.execution_authorized
                for item in metrics
            ),
            state_mutations=sum(
                item.state_mutations
                for item in metrics
            ),
        )


__all__ = [
    "OperatorMetrics",
    "OperatorMetricsEngine",
    "OperatorMetricsError",
]
