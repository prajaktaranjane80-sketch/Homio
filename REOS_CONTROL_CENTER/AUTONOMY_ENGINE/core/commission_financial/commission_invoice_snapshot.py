from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..contract_primitives import fingerprint
from .commission_invoice import CommissionInvoice


@dataclass(frozen=True, slots=True)
class CommissionInvoiceSnapshot:
    invoice_id: str
    tenant_id: str
    commission_id: str
    invoice_version: int
    canonical_payload: dict[str, Any]
    snapshot_fingerprint: str

    @classmethod
    def from_invoice(
        cls,
        invoice: CommissionInvoice,
    ) -> "CommissionInvoiceSnapshot":
        if not isinstance(
            invoice,
            CommissionInvoice,
        ):
            raise TypeError(
                "invoice must be CommissionInvoice."
            )

        payload = invoice.to_dict(
            include_fingerprint=False
        )

        return cls(
            invoice_id=invoice.invoice_id,
            tenant_id=invoice.tenant_id,
            commission_id=invoice.commission_id,
            invoice_version=(
                invoice.invoice_version
            ),
            canonical_payload=payload,
            snapshot_fingerprint=fingerprint(
                payload
            ),
        )

    def verify(self) -> bool:
        return (
            self.snapshot_fingerprint
            == fingerprint(
                self.canonical_payload
            )
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "invoice_id": self.invoice_id,
            "tenant_id": self.tenant_id,
            "commission_id": self.commission_id,
            "invoice_version": (
                self.invoice_version
            ),
            "canonical_payload": dict(
                self.canonical_payload
            ),
            "snapshot_fingerprint": (
                self.snapshot_fingerprint
            ),
        }


__all__ = [
    "CommissionInvoiceSnapshot",
]
