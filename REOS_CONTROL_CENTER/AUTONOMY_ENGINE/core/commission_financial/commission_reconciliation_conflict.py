from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .commission_reconciliation import (
    CommissionReconciliation,
)


class CommissionReconciliationConflictError(
    ValueError
):
    """Conflicting reconciliation result."""


@dataclass(frozen=True, slots=True)
class CommissionReconciliationComparison:
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


def compare_reconciliations(
    left: CommissionReconciliation,
    right: CommissionReconciliation,
) -> CommissionReconciliationComparison:
    if (
        not isinstance(
            left,
            CommissionReconciliation,
        )
        or not isinstance(
            right,
            CommissionReconciliation,
        )
    ):
        raise CommissionReconciliationConflictError(
            "Both values must be CommissionReconciliation."
        )

    same_identity = (
        left.tenant_id
        == right.tenant_id
        and left.reconciliation_id
        == right.reconciliation_id
        and left.reconciliation_version
        == right.reconciliation_version
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

    return CommissionReconciliationComparison(
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
    left: CommissionReconciliation,
    right: CommissionReconciliation,
) -> None:
    comparison = compare_reconciliations(
        left,
        right,
    )

    if (
        comparison.same_identity
        and not comparison.same_fingerprint
    ):
        raise CommissionReconciliationConflictError(
            "Same reconciliation identity contains "
            "conflicting financial results."
        )


__all__ = [
    "CommissionReconciliationConflictError",
    "CommissionReconciliationComparison",
    "compare_reconciliations",
    "assert_no_conflict",
]
