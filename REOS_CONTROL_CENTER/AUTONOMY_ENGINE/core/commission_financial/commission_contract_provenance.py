from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from .commission_contract import (
    CommissionContract,
    CommissionContractProvenance,
)


@dataclass(frozen=True, slots=True)
class CommissionProvenanceRecord:
    """Immutable derived provenance record for one contract version."""

    tenant_id: str
    commission_id: str
    contract_version: int
    provenance: CommissionContractProvenance

    def __post_init__(self) -> None:
        if not isinstance(
            self.tenant_id,
            str,
        ) or not self.tenant_id.strip():
            raise ValueError(
                "tenant_id must be non-empty."
            )

        if not isinstance(
            self.commission_id,
            str,
        ) or not self.commission_id.strip():
            raise ValueError(
                "commission_id must be non-empty."
            )

        if (
            isinstance(
                self.contract_version,
                bool,
            )
            or not isinstance(
                self.contract_version,
                int,
            )
            or self.contract_version < 1
        ):
            raise ValueError(
                "contract_version must be positive."
            )

        if not isinstance(
            self.provenance,
            CommissionContractProvenance,
        ):
            raise TypeError(
                "provenance must be CommissionContractProvenance."
            )

    @property
    def identity_key(self) -> tuple[
        str,
        str,
        int,
    ]:
        return (
            self.tenant_id,
            self.commission_id,
            self.contract_version,
        )

    @classmethod
    def from_contract(
        cls,
        contract: CommissionContract,
    ) -> "CommissionProvenanceRecord":
        if not isinstance(
            contract,
            CommissionContract,
        ):
            raise TypeError(
                "contract must be CommissionContract."
            )

        return cls(
            tenant_id=contract.tenant_id,
            commission_id=contract.commission_id,
            contract_version=contract.contract_version,
            provenance=contract.provenance,
        )

    def assert_scope(
        self,
        *,
        tenant_id: str,
        commission_id: str,
    ) -> None:
        if (
            self.tenant_id != tenant_id
            or self.commission_id != commission_id
        ):
            raise ValueError(
                "Commission provenance crossed identity scope."
            )

    def to_dict(self) -> dict[str, object]:
        return {
            "tenant_id": self.tenant_id,
            "commission_id": self.commission_id,
            "contract_version": self.contract_version,
            "provenance": self.provenance.to_dict(),
        }


def provenance_is_before_effective_start(
    contract: CommissionContract,
) -> bool:
    """Verify that evidence existed no later than contract activation."""

    return (
        contract.provenance.captured_at
        <= contract.effective_from
    )


def provenance_timestamp(
    contract: CommissionContract,
) -> datetime:
    return contract.provenance.captured_at


__all__ = [
    "CommissionProvenanceRecord",
    "provenance_is_before_effective_start",
    "provenance_timestamp",
]
