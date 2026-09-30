from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..contract_primitives import fingerprint
from .commission_dispute import CommissionDispute


@dataclass(frozen=True, slots=True)
class CommissionDisputeSnapshot:
    dispute_id: str
    tenant_id: str
    commission_id: str
    settlement_id: str
    dispute_version: int
    canonical_payload: dict[str, Any]
    snapshot_fingerprint: str

    @classmethod
    def from_dispute(
        cls,
        dispute: CommissionDispute,
    ) -> "CommissionDisputeSnapshot":
        if not isinstance(
            dispute,
            CommissionDispute,
        ):
            raise TypeError(
                "dispute must be CommissionDispute."
            )

        payload = dispute.to_dict(
            include_fingerprint=False
        )

        return cls(
            dispute_id=dispute.dispute_id,
            tenant_id=dispute.tenant_id,
            commission_id=dispute.commission_id,
            settlement_id=dispute.settlement_id,
            dispute_version=dispute.dispute_version,
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
            "dispute_id": self.dispute_id,
            "tenant_id": self.tenant_id,
            "commission_id": self.commission_id,
            "settlement_id": self.settlement_id,
            "dispute_version": self.dispute_version,
            "canonical_payload": dict(
                self.canonical_payload
            ),
            "snapshot_fingerprint": (
                self.snapshot_fingerprint
            ),
        }


__all__ = [
    "CommissionDisputeSnapshot",
]
