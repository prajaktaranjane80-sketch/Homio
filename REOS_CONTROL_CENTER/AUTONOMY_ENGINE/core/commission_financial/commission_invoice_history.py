from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .commission_invoice import CommissionInvoice


class CommissionInvoiceHistoryError(
    ValueError
):
    """Invalid invoice history."""


@dataclass(frozen=True, slots=True)
class CommissionInvoiceHistoryEntry:
    invoice_id: str
    tenant_id: str
    commission_id: str
    invoice_version: int
    invoice_number: str
    state: str
    total_due: str
    invoice_fingerprint: str

    @classmethod
    def from_invoice(
        cls,
        invoice: CommissionInvoice,
    ) -> "CommissionInvoiceHistoryEntry":
        if not isinstance(
            invoice,
            CommissionInvoice,
        ):
            raise CommissionInvoiceHistoryError(
                "invoice must be CommissionInvoice."
            )

        return cls(
            invoice_id=invoice.invoice_id,
            tenant_id=invoice.tenant_id,
            commission_id=invoice.commission_id,
            invoice_version=(
                invoice.invoice_version
            ),
            invoice_number=invoice.invoice_number,
            state=invoice.state.value,
            total_due=format(
                invoice.total_due.amount,
                "f",
            ),
            invoice_fingerprint=(
                invoice.immutable_fingerprint
            ),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "invoice_id": self.invoice_id,
            "tenant_id": self.tenant_id,
            "commission_id": self.commission_id,
            "invoice_version": (
                self.invoice_version
            ),
            "invoice_number": (
                self.invoice_number
            ),
            "state": self.state,
            "total_due": self.total_due,
            "invoice_fingerprint": (
                self.invoice_fingerprint
            ),
        }


@dataclass(frozen=True, slots=True)
class CommissionInvoiceHistory:
    entries: tuple[
        CommissionInvoiceHistoryEntry,
        ...
    ] = ()

    def append(
        self,
        invoice: CommissionInvoice,
    ) -> "CommissionInvoiceHistory":
        entry = (
            CommissionInvoiceHistoryEntry
            .from_invoice(invoice)
        )

        if self.entries:
            latest = self.entries[-1]

            if (
                latest.tenant_id
                != entry.tenant_id
                or latest.invoice_id
                != entry.invoice_id
            ):
                raise CommissionInvoiceHistoryError(
                    "Invoice history identity mismatch."
                )

            if (
                entry.invoice_version
                != latest.invoice_version + 1
            ):
                if (
                    entry.invoice_version
                    == latest.invoice_version
                    and entry.invoice_fingerprint
                    == latest.invoice_fingerprint
                ):
                    return self

                raise CommissionInvoiceHistoryError(
                    "Invoice versions must advance sequentially."
                )

        elif entry.invoice_version != 1:
            raise CommissionInvoiceHistoryError(
                "First invoice version must be 1."
            )

        return CommissionInvoiceHistory(
            entries=self.entries + (entry,)
        )

    @property
    def latest(
        self,
    ) -> CommissionInvoiceHistoryEntry | None:
        return (
            self.entries[-1]
            if self.entries
            else None
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "entries": [
                entry.to_dict()
                for entry in self.entries
            ]
        }


__all__ = [
    "CommissionInvoiceHistoryError",
    "CommissionInvoiceHistoryEntry",
    "CommissionInvoiceHistory",
]
