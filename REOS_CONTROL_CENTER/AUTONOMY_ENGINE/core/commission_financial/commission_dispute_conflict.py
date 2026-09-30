from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .commission_dispute import CommissionDispute


class CommissionDisputeConflictError(
    ValueError
):
    """Conflicting dispute versions."""


@dataclass(frozen=True, slots=True)
class CommissionDisputeComparison:
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


def compare_disputes(
    left: CommissionDispute,
    right: CommissionDispute,
) -> CommissionDisputeComparison:
    if (
        not isinstance(
            left,
            CommissionDispute,
        )
        or not isinstance(
            right,
            CommissionDispute,
        )
    ):
        raise CommissionDisputeConflictError(
            "Both values must be CommissionDispute."
        )

    same_identity = (
        left.tenant_id
        == right.tenant_id
        and left.dispute_id
        == right.dispute_id
        and left.dispute_version
        == right.dispute_version
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

    return CommissionDisputeComparison(
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
    left: CommissionDispute,
    right: CommissionDispute,
) -> None:
    comparison = compare_disputes(
        left,
        right,
    )

    if (
        comparison.same_identity
        and not comparison.same_fingerprint
    ):
        raise CommissionDisputeConflictError(
            "Same dispute identity/version contains "
            "conflicting financial state."
        )


__all__ = [
    "CommissionDisputeConflictError",
    "CommissionDisputeComparison",
    "compare_disputes",
    "assert_no_conflict",
]
