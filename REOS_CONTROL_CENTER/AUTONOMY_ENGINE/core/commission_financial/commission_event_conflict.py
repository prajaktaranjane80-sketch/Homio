from __future__ import annotations

from dataclasses import dataclass

from ..event_platform.event_domain import EventEnvelope


@dataclass(frozen=True, slots=True)
class CommissionFinancialEventComparison:
    same_identity: bool
    same_fingerprint: bool
    conflict: bool
    left_fingerprint: str
    right_fingerprint: str

    def to_dict(self) -> dict[str, bool | str]:
        return {
            "same_identity": self.same_identity,
            "same_fingerprint": self.same_fingerprint,
            "conflict": self.conflict,
            "left_fingerprint": self.left_fingerprint,
            "right_fingerprint": self.right_fingerprint,
        }


class CommissionFinancialEventConflictError(
    ValueError
):
    """Conflicting immutable financial event identity."""


def compare_financial_events(
    left: EventEnvelope,
    right: EventEnvelope,
) -> CommissionFinancialEventComparison:
    if not isinstance(
        left,
        EventEnvelope,
    ):
        raise TypeError(
            "left must be EventEnvelope"
        )

    if not isinstance(
        right,
        EventEnvelope,
    ):
        raise TypeError(
            "right must be EventEnvelope"
        )

    same_identity = (
        left.tenant_id == right.tenant_id
        and left.event_id == right.event_id
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

    return CommissionFinancialEventComparison(
        same_identity=same_identity,
        same_fingerprint=same_fingerprint,
        conflict=(
            same_identity
            and not same_fingerprint
        ),
        left_fingerprint=left_fingerprint,
        right_fingerprint=right_fingerprint,
    )


def assert_no_event_conflict(
    left: EventEnvelope,
    right: EventEnvelope,
) -> None:
    comparison = compare_financial_events(
        left,
        right,
    )

    if comparison.conflict:
        raise CommissionFinancialEventConflictError(
            "Same CORE-008 financial event identity "
            "contains different immutable content."
        )


__all__ = [
    "CommissionFinancialEventComparison",
    "CommissionFinancialEventConflictError",
    "compare_financial_events",
    "assert_no_event_conflict",
]
