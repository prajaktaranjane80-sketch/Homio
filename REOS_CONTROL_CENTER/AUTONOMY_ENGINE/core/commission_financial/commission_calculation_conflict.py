from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .commission_calculation import (
    CommissionCalculation,
)


class CommissionCalculationConflictError(
    ValueError
):
    """Same calculation identity contains conflicting results."""


@dataclass(frozen=True, slots=True)
class CommissionCalculationComparison:
    same_identity: bool
    same_fingerprint: bool
    identical: bool
    left_fingerprint: str
    right_fingerprint: str

    def __post_init__(self) -> None:
        expected = (
            self.same_identity
            and self.same_fingerprint
        )

        if self.identical != expected:
            raise ValueError(
                "identical comparison is inconsistent."
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "same_identity": (
                self.same_identity
            ),
            "same_fingerprint": (
                self.same_fingerprint
            ),
            "identical": self.identical,
            "left_fingerprint": (
                self.left_fingerprint
            ),
            "right_fingerprint": (
                self.right_fingerprint
            ),
        }


def compare_calculations(
    left: CommissionCalculation,
    right: CommissionCalculation,
) -> CommissionCalculationComparison:
    if (
        not isinstance(
            left,
            CommissionCalculation,
        )
        or not isinstance(
            right,
            CommissionCalculation,
        )
    ):
        raise CommissionCalculationConflictError(
            "Both values must be CommissionCalculation."
        )

    same_identity = (
        left.identity_key
        == right.identity_key
    )

    left_fingerprint = (
        left.immutable_fingerprint
    )

    right_fingerprint = (
        right.immutable_fingerprint
    )

    same_fingerprint = (
        left_fingerprint
        == right_fingerprint
    )

    return CommissionCalculationComparison(
        same_identity=same_identity,
        same_fingerprint=same_fingerprint,
        identical=(
            same_identity
            and same_fingerprint
        ),
        left_fingerprint=left_fingerprint,
        right_fingerprint=right_fingerprint,
    )


def assert_no_conflict(
    left: CommissionCalculation,
    right: CommissionCalculation,
) -> None:
    comparison = compare_calculations(
        left,
        right,
    )

    if (
        comparison.same_identity
        and not comparison.same_fingerprint
    ):
        raise CommissionCalculationConflictError(
            "Same tenant/commission/contract/"
            "calculation version has conflicting results."
        )


__all__ = [
    "CommissionCalculationConflictError",
    "CommissionCalculationComparison",
    "compare_calculations",
    "assert_no_conflict",
]
