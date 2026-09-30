from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from .commission_invoice import (
    CommissionInvoice,
    CommissionInvoiceState,
)
from .commission_settlement import CommissionSettlement


def validate_invoice(
    invoice: CommissionInvoice,
    settlement: CommissionSettlement,
    *,
    at: datetime,
) -> tuple[str, ...]:
    errors: list[str] = []

    if not isinstance(
        invoice,
        CommissionInvoice,
    ):
        return ("invoice must be CommissionInvoice.",)

    if not isinstance(
        settlement,
        CommissionSettlement,
    ):
        return (
            "settlement must be CommissionSettlement.",
        )

    if invoice.tenant_id != settlement.tenant_id:
        errors.append("tenant mismatch")

    if invoice.commission_id != settlement.commission_id:
        errors.append("commission mismatch")

    if invoice.settlement_id != settlement.settlement_id:
        errors.append("settlement mismatch")

    if (
        invoice.total_due.currency.identity_key
        != settlement.amount.currency.identity_key
    ):
        errors.append("invoice currency mismatch")

    if (
        invoice.total_due.amount
        < Decimal("0")
    ):
        errors.append("invoice total cannot be negative")

    if invoice.due_at < invoice.issued_at:
        errors.append(
            "due_at cannot precede issued_at"
        )

    if invoice.issued_at > at:
        errors.append(
            "invoice cannot be issued after validation time"
        )

    if (
        invoice.state is CommissionInvoiceState.PAID
        and invoice.total_due.amount == 0
    ):
        errors.append(
            "zero-value invoice cannot be represented "
            "as a paid obligation"
        )

    return tuple(errors)


def invoice_validation_report(
    invoice: CommissionInvoice,
    settlement: CommissionSettlement,
    *,
    at: datetime,
) -> dict[str, Any]:
    errors = validate_invoice(
        invoice,
        settlement,
        at=at,
    )

    return {
        "valid": not errors,
        "errors": errors,
    }


__all__ = [
    "validate_invoice",
    "invoice_validation_report",
]
