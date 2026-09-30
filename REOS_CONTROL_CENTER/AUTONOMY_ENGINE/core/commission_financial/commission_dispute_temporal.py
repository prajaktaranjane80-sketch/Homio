from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from .commission_dispute import CommissionDispute
from .commission_settlement import CommissionSettlement


class CommissionDisputeTemporalError(
    ValueError
):
    """Invalid dispute temporal relationship."""


def _normalize(
    value: datetime,
    field: str,
) -> datetime:
    if (
        not isinstance(value, datetime)
        or value.tzinfo is None
        or value.utcoffset() is None
    ):
        raise CommissionDisputeTemporalError(
            f"{field} must be timezone-aware."
        )

    return value.astimezone(timezone.utc)


@dataclass(frozen=True, slots=True)
class DisputeTemporalWindow:
    valid_from: datetime
    valid_to: datetime | None = None

    def __post_init__(self) -> None:
        start = _normalize(
            self.valid_from,
            "valid_from",
        )

        object.__setattr__(
            self,
            "valid_from",
            start,
        )

        if self.valid_to is not None:
            end = _normalize(
                self.valid_to,
                "valid_to",
            )

            if end <= start:
                raise CommissionDisputeTemporalError(
                    "valid_to must be later than valid_from."
                )

            object.__setattr__(
                self,
                "valid_to",
                end,
            )

    def contains(
        self,
        at: datetime,
    ) -> bool:
        instant = _normalize(
            at,
            "at",
        )

        if instant < self.valid_from:
            return False

        return (
            self.valid_to is None
            or instant < self.valid_to
        )


def assert_dispute_temporal_order(
    settlement: CommissionSettlement,
    dispute: CommissionDispute,
) -> None:
    if dispute.opened_at < settlement.requested_at:
        raise CommissionDisputeTemporalError(
            "Dispute cannot be opened before "
            "the settlement request."
        )


__all__ = [
    "CommissionDisputeTemporalError",
    "DisputeTemporalWindow",
    "assert_dispute_temporal_order",
]
