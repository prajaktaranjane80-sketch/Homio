from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from .commission_invoice import CommissionInvoice
from .commission_settlement import CommissionSettlement


class CommissionInvoiceTemporalError(
    ValueError
):
    """Invalid invoice temporal relationship."""


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
        raise CommissionInvoiceTemporalError(
            f"{field} must be timezone-aware."
        )

    return value.astimezone(timezone.utc)


@dataclass(frozen=True, slots=True)
class InvoiceTemporalWindow:
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
                raise CommissionInvoiceTemporalError(
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


def assert_invoice_temporal_order(
    settlement: CommissionSettlement,
    invoice: CommissionInvoice,
) -> None:
    if invoice.issued_at < settlement.requested_at:
        raise CommissionInvoiceTemporalError(
            "Invoice cannot be issued before settlement request."
        )

    if invoice.due_at < invoice.issued_at:
        raise CommissionInvoiceTemporalError(
            "Invoice due date cannot precede issue date."
        )


__all__ = [
    "CommissionInvoiceTemporalError",
    "InvoiceTemporalWindow",
    "assert_invoice_temporal_order",
]
