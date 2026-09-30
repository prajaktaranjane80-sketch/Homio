from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .commission_tax import CommissionTaxAssessment


class CommissionTaxConflictError(
    ValueError
):
    """Conflicting tax assessment."""


@dataclass(frozen=True, slots=True)
class CommissionTaxComparison:
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
            "same_identity": self.same_identity,
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


def compare_tax_assessments(
    left: CommissionTaxAssessment,
    right: CommissionTaxAssessment,
) -> CommissionTaxComparison:
    if (
        not isinstance(
            left,
            CommissionTaxAssessment,
        )
        or not isinstance(
            right,
            CommissionTaxAssessment,
        )
    ):
        raise CommissionTaxConflictError(
            "Both values must be CommissionTaxAssessment."
        )

    same_identity = (
        left.tenant_id
        == right.tenant_id
        and left.assessment_id
        == right.assessment_id
        and left.assessment_version
        == right.assessment_version
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

    return CommissionTaxComparison(
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
    left: CommissionTaxAssessment,
    right: CommissionTaxAssessment,
) -> None:
    comparison = compare_tax_assessments(
        left,
        right,
    )

    if (
        comparison.same_identity
        and not comparison.same_fingerprint
    ):
        raise CommissionTaxConflictError(
            "Same tax assessment identity/version "
            "contains conflicting tax results."
        )


__all__ = [
    "CommissionTaxConflictError",
    "CommissionTaxComparison",
    "compare_tax_assessments",
    "assert_no_conflict",
]
