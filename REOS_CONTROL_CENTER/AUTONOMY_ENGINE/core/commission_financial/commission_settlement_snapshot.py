from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..contract_primitives import fingerprint
from .commission_settlement import CommissionSettlement


@dataclass(frozen=True, slots=True)
class CommissionSettlementSnapshot:
    settlement_id: str
    tenant_id: str
    commission_id: str
    allocation_set_id: str
    settlement_version: int
    canonical_payload: dict[str, Any]
    snapshot_fingerprint: str

    @classmethod
    def from_settlement(
        cls,
        settlement: CommissionSettlement,
    ) -> "CommissionSettlementSnapshot":
        if not isinstance(
            settlement,
            CommissionSettlement,
        ):
            raise TypeError(
                "settlement must be CommissionSettlement."
            )

        payload = settlement.to_dict(
            include_fingerprint=False
        )

        return cls(
            settlement_id=(
                settlement.settlement_id
            ),
            tenant_id=settlement.tenant_id,
            commission_id=(
                settlement.commission_id
            ),
            allocation_set_id=(
                settlement.allocation_set_id
            ),
            settlement_version=(
                settlement.settlement_version
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
            "settlement_id": (
                self.settlement_id
            ),
            "tenant_id": self.tenant_id,
            "commission_id": (
                self.commission_id
            ),
            "allocation_set_id": (
                self.allocation_set_id
            ),
            "settlement_version": (
                self.settlement_version
            ),
            "canonical_payload": dict(
                self.canonical_payload
            ),
            "snapshot_fingerprint": (
                self.snapshot_fingerprint
            ),
        }


__all__ = [
    "CommissionSettlementSnapshot",
]
