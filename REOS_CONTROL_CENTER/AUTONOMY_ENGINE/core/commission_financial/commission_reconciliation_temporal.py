from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from .commission_reconciliation import (
    CommissionExternalSettlementEvidence,
    CommissionReconciliation,
)
from .commission_settlement import CommissionSettlement


class CommissionReconciliationTemporalError(
    ValueError
):
    """Invalid reconciliation temporal relationship."""


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
        raise CommissionReconciliationTemporalError(
            f"{field} must be timezone-aware."
        )

    return value.astimezone(timezone.utc)


@dataclass(frozen=True, slots=True)
class ReconciliationTemporalWindow:
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
                raise CommissionReconciliationTemporalError(
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


def assert_reconciliation_temporal_order(
    settlement: CommissionSettlement,
    evidence: CommissionExternalSettlementEvidence,
    reconciliation: CommissionReconciliation,
) -> None:
    if evidence.observed_at < settlement.requested_at:
        raise CommissionReconciliationTemporalError(
            "External settlement evidence cannot precede "
            "the settlement request."
        )

    if reconciliation.reconciled_at < evidence.observed_at:
        raise CommissionReconciliationTemporalError(
            "Reconciliation cannot precede external "
            "evidence observation."
        )


__all__ = [
    "CommissionReconciliationTemporalError",
    "ReconciliationTemporalWindow",
    "assert_reconciliation_temporal_order",
]
