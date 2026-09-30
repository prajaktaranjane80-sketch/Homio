from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..contract_primitives import fingerprint
from .commission_allocation import (
    CommissionAllocation,
)


@dataclass(frozen=True, slots=True)
class CommissionAllocationSnapshot:
    allocation_set_id: str
    tenant_id: str
    commission_id: str
    calculation_id: str
    canonical_payload: dict[str, Any]
    snapshot_fingerprint: str

    @classmethod
    def from_allocation(
        cls,
        allocation: CommissionAllocation,
    ) -> "CommissionAllocationSnapshot":
        if not isinstance(
            allocation,
            CommissionAllocation,
        ):
            raise TypeError(
                "allocation must be CommissionAllocation."
            )

        payload = allocation.to_dict(
            include_fingerprint=False
        )

        return cls(
            allocation_set_id=(
                allocation.allocation_set_id
            ),
            tenant_id=allocation.tenant_id,
            commission_id=(
                allocation.commission_id
            ),
            calculation_id=(
                allocation.calculation_id
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
            "allocation_set_id": (
                self.allocation_set_id
            ),
            "tenant_id": self.tenant_id,
            "commission_id": (
                self.commission_id
            ),
            "calculation_id": (
                self.calculation_id
            ),
            "canonical_payload": dict(
                self.canonical_payload
            ),
            "snapshot_fingerprint": (
                self.snapshot_fingerprint
            ),
        }


__all__ = [
    "CommissionAllocationSnapshot",
]
