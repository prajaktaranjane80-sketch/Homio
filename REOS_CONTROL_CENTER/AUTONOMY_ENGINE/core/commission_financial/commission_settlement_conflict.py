from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .commission_settlement import CommissionSettlement


class CommissionSettlementConflictError(
    ValueError
):
    """Same settlement identity contains conflicting terms."""


@dataclass(frozen=True, slots=True)
class CommissionSettlementComparison:
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


def compare_settlements(
    left: CommissionSettlement,
    right: CommissionSettlement,
) -> CommissionSettlementComparison:
    if (
        not isinstance(
            left,
            CommissionSettlement,
        )
        or not isinstance(
            right,
            CommissionSettlement,
        )
    ):
        raise CommissionSettlementConflictError(
            "Both values must be CommissionSettlement."
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

    return CommissionSettlementComparison(
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
    left: CommissionSettlement,
    right: CommissionSettlement,
) -> None:
    comparison = compare_settlements(
        left,
        right,
    )

    if (
        comparison.same_identity
        and not comparison.same_fingerprint
    ):
        raise CommissionSettlementConflictError(
            "Same settlement identity contains "
            "conflicting financial instructions."
        )


__all__ = [
    "CommissionSettlementConflictError",
    "CommissionSettlementComparison",
    "compare_settlements",
    "assert_no_conflict",
]
