from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..contract_primitives import fingerprint
from .commission_reconciliation import (
    CommissionReconciliation,
)


@dataclass(frozen=True, slots=True)
class CommissionReconciliationSnapshot:
    reconciliation_id: str
    tenant_id: str
    commission_id: str
    settlement_id: str
    reconciliation_version: int
    canonical_payload: dict[str, Any]
    snapshot_fingerprint: str

    @classmethod
    def from_reconciliation(
        cls,
        reconciliation: CommissionReconciliation,
    ) -> "CommissionReconciliationSnapshot":
        if not isinstance(
            reconciliation,
            CommissionReconciliation,
        ):
            raise TypeError(
                "reconciliation must be "
                "CommissionReconciliation."
            )

        payload = reconciliation.to_dict(
            include_fingerprint=False
        )

        return cls(
            reconciliation_id=(
                reconciliation.reconciliation_id
            ),
            tenant_id=reconciliation.tenant_id,
            commission_id=(
                reconciliation.commission_id
            ),
            settlement_id=(
                reconciliation.settlement_id
            ),
            reconciliation_version=(
                reconciliation.reconciliation_version
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
            "reconciliation_id": (
                self.reconciliation_id
            ),
            "tenant_id": self.tenant_id,
            "commission_id": (
                self.commission_id
            ),
            "settlement_id": (
                self.settlement_id
            ),
            "reconciliation_version": (
                self.reconciliation_version
            ),
            "canonical_payload": dict(
                self.canonical_payload
            ),
            "snapshot_fingerprint": (
                self.snapshot_fingerprint
            ),
        }


__all__ = [
    "CommissionReconciliationSnapshot",
]
