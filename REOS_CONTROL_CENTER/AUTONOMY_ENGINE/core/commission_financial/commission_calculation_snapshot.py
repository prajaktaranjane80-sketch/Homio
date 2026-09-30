from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..contract_primitives import fingerprint
from .commission_calculation import (
    CommissionCalculation,
)


@dataclass(frozen=True, slots=True)
class CommissionCalculationSnapshot:
    """Canonical immutable calculation snapshot."""

    calculation_id: str
    tenant_id: str
    commission_id: str
    contract_version: int
    calculation_version: int
    canonical_payload: dict[str, Any]
    snapshot_fingerprint: str

    @classmethod
    def from_calculation(
        cls,
        calculation: CommissionCalculation,
    ) -> "CommissionCalculationSnapshot":
        if not isinstance(
            calculation,
            CommissionCalculation,
        ):
            raise TypeError(
                "calculation must be CommissionCalculation."
            )

        payload = calculation.to_dict(
            include_fingerprint=False
        )

        return cls(
            calculation_id=(
                calculation.calculation_id
            ),
            tenant_id=calculation.tenant_id,
            commission_id=(
                calculation.commission_id
            ),
            contract_version=(
                calculation.contract_version
            ),
            calculation_version=(
                calculation.calculation_version
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
            "calculation_id": (
                self.calculation_id
            ),
            "tenant_id": self.tenant_id,
            "commission_id": (
                self.commission_id
            ),
            "contract_version": (
                self.contract_version
            ),
            "calculation_version": (
                self.calculation_version
            ),
            "canonical_payload": dict(
                self.canonical_payload
            ),
            "snapshot_fingerprint": (
                self.snapshot_fingerprint
            ),
        }


__all__ = [
    "CommissionCalculationSnapshot",
]
