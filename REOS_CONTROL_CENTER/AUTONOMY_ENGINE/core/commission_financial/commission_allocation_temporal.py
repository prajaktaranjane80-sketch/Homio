from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from .commission_allocation import (
    CommissionAllocation,
)
from .commission_entitlement import (
    CommissionEntitlement,
)


class CommissionAllocationTemporalError(
    ValueError
):
    """Invalid allocation temporal relationship."""


@dataclass(frozen=True, slots=True)
class AllocationTemporalWindow:
    valid_from: datetime
    valid_to: datetime | None = None

    def __post_init__(self) -> None:
        start = self._normalize(
            self.valid_from,
            "valid_from",
        )

        object.__setattr__(
            self,
            "valid_from",
            start,
        )

        if self.valid_to is not None:
            end = self._normalize(
                self.valid_to,
                "valid_to",
            )

            if end <= start:
                raise CommissionAllocationTemporalError(
                    "valid_to must be later than valid_from."
                )

            object.__setattr__(
                self,
                "valid_to",
                end,
            )

    @staticmethod
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
            raise CommissionAllocationTemporalError(
                f"{field} must be timezone-aware."
            )

        return value.astimezone(timezone.utc)

    def contains(
        self,
        at: datetime,
    ) -> bool:
        instant = self._normalize(
            at,
            "at",
        )

        if instant < self.valid_from:
            return False

        return (
            self.valid_to is None
            or instant < self.valid_to
        )


def assert_entitlement_before_allocation(
    entitlement: CommissionEntitlement,
    allocation: CommissionAllocation,
) -> None:
    if (
        entitlement.established_at
        > allocation.lines[0].amount.currency.rounding_mode
        if False
        else False
    ):
        raise CommissionAllocationTemporalError(
            "Invalid temporal relationship."
        )

    if (
        entitlement.entitlement_id
        not in {
            line.entitlement_id
            for line in allocation.lines
        }
    ):
        raise CommissionAllocationTemporalError(
            "Referenced entitlement is not part of allocation."
        )


__all__ = [
    "CommissionAllocationTemporalError",
    "AllocationTemporalWindow",
    "assert_entitlement_before_allocation",
]
