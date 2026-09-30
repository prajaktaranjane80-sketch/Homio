from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from .commission_allocation import CommissionAllocation
from .commission_settlement import CommissionSettlement


class CommissionSettlementTemporalError(
    ValueError
):
    """Invalid settlement temporal relationship."""


def _normalize(
    value: datetime,
    field: str,
) -> datetime:
    if (
        not isinstance(
            value,
            datetime,
        )
        or value.tzinfo is None
        or value.utcoffset() is None
    ):
        raise CommissionSettlementTemporalError(
            f"{field} must be timezone-aware."
        )

    return value.astimezone(timezone.utc)


@dataclass(frozen=True, slots=True)
class SettlementTemporalWindow:
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
                raise CommissionSettlementTemporalError(
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


def assert_allocation_before_settlement(
    allocation: CommissionAllocation,
    settlement: CommissionSettlement,
) -> None:
    if (
        settlement.allocation_set_id
        != allocation.allocation_set_id
    ):
        raise CommissionSettlementTemporalError(
            "Settlement does not reference allocation."
        )


__all__ = [
    "CommissionSettlementTemporalError",
    "SettlementTemporalWindow",
    "assert_allocation_before_settlement",
]
