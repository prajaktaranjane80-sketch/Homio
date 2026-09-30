from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .commission_invoice import CommissionInvoice
from .commission_invoice_snapshot import (
    CommissionInvoiceSnapshot,
)


class CommissionInvoiceIntegrityError(
    ValueError
):
    """Invoice integrity failure."""


@dataclass(frozen=True, slots=True)
class CommissionInvoiceIntegrityReport:
    valid: bool
    invoice_fingerprint: str
    snapshot_fingerprint: str
    reasons: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "valid": self.valid,
            "invoice_fingerprint": (
                self.invoice_fingerprint
            ),
            "snapshot_fingerprint": (
                self.snapshot_fingerprint
            ),
            "reasons": list(self.reasons),
        }


def inspect_integrity(
    invoice: CommissionInvoice,
    snapshot: CommissionInvoiceSnapshot,
) -> CommissionInvoiceIntegrityReport:
    if not isinstance(
        invoice,
        CommissionInvoice,
    ):
        raise CommissionInvoiceIntegrityError(
            "invoice must be CommissionInvoice."
        )

    if not isinstance(
        snapshot,
        CommissionInvoiceSnapshot,
    ):
        raise CommissionInvoiceIntegrityError(
            "snapshot must be CommissionInvoiceSnapshot."
        )

    reasons: list[str] = []

    current_fingerprint = (
        invoice.immutable_fingerprint
    )

    if (
        invoice.invoice_id
        != snapshot.invoice_id
    ):
        reasons.append(
            "invoice_id mismatch"
        )

    if (
        invoice.tenant_id
        != snapshot.tenant_id
    ):
        reasons.append(
            "tenant_id mismatch"
        )

    if (
        invoice.commission_id
        != snapshot.commission_id
    ):
        reasons.append(
            "commission_id mismatch"
        )

    if (
        invoice.invoice_version
        != snapshot.invoice_version
    ):
        reasons.append(
            "invoice_version mismatch"
        )

    if not snapshot.verify():
        reasons.append(
            "snapshot fingerprint is invalid"
        )

    regenerated = (
        CommissionInvoiceSnapshot
        .from_invoice(invoice)
    )

    if (
        regenerated.snapshot_fingerprint
        != snapshot.snapshot_fingerprint
    ):
        reasons.append(
            "invoice does not match snapshot"
        )

    return CommissionInvoiceIntegrityReport(
        valid=not reasons,
        invoice_fingerprint=(
            current_fingerprint
        ),
        snapshot_fingerprint=(
            snapshot.snapshot_fingerprint
        ),
        reasons=tuple(reasons),
    )


def assert_integrity(
    invoice: CommissionInvoice,
    snapshot: CommissionInvoiceSnapshot,
) -> None:
    report = inspect_integrity(
        invoice,
        snapshot,
    )

    if not report.valid:
        raise CommissionInvoiceIntegrityError(
            "; ".join(report.reasons)
        )


__all__ = [
    "CommissionInvoiceIntegrityError",
    "CommissionInvoiceIntegrityReport",
    "inspect_integrity",
    "assert_integrity",
]
