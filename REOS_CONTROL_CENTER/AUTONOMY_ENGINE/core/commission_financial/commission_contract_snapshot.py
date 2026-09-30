from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from ..contract_primitives import deep_freeze, fingerprint
from .commission_contract import CommissionContract


class CommissionContractSnapshotError(
    ValueError
):
    """Base immutable commission-contract snapshot error."""


class CommissionContractSnapshotIntegrityError(
    CommissionContractSnapshotError
):
    """Snapshot integrity validation failed."""


@dataclass(frozen=True, slots=True)
class CommissionContractSnapshot:
    """Immutable derived snapshot of commission terms.

    This is evidence/history material only.

    It is NOT:
    - a second commission source of truth,
    - a mutable contract store,
    - a calculation engine,
    - an allocation engine,
    - a ledger,
    - a settlement engine,
    - an event store,
    - an ACRL checkpoint store.
    """

    tenant_id: str
    commission_id: str
    contract_version: int
    terms: Mapping[str, Any]
    terms_fingerprint: str

    def __post_init__(self) -> None:
        if not isinstance(
            self.tenant_id,
            str,
        ) or not self.tenant_id.strip():
            raise CommissionContractSnapshotError(
                "tenant_id must be non-empty."
            )

        if not isinstance(
            self.commission_id,
            str,
        ) or not self.commission_id.strip():
            raise CommissionContractSnapshotError(
                "commission_id must be non-empty."
            )

        if (
            isinstance(self.contract_version, bool)
            or not isinstance(
                self.contract_version,
                int,
            )
            or self.contract_version < 1
        ):
            raise CommissionContractSnapshotError(
                "contract_version must be positive."
            )

        if not isinstance(
            self.terms,
            Mapping,
        ):
            raise CommissionContractSnapshotError(
                "terms must be a mapping."
            )

        frozen_terms = deep_freeze(
            dict(self.terms),
            field_name="terms",
        )

        object.__setattr__(
            self,
            "terms",
            frozen_terms,
        )

        derived = fingerprint(
            dict(self.terms)
        )

        if derived != self.terms_fingerprint:
            raise CommissionContractSnapshotIntegrityError(
                "Snapshot fingerprint does not match terms."
            )

    @classmethod
    def from_contract(
        cls,
        contract: CommissionContract,
    ) -> "CommissionContractSnapshot":
        if not isinstance(
            contract,
            CommissionContract,
        ):
            raise CommissionContractSnapshotError(
                "contract must be CommissionContract."
            )

        terms = contract.to_dict(
            include_fingerprint=False
        )

        return cls(
            tenant_id=contract.tenant_id,
            commission_id=contract.commission_id,
            contract_version=contract.contract_version,
            terms=terms,
            terms_fingerprint=fingerprint(
                terms
            ),
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

    def assert_matches_contract(
        self,
        contract: CommissionContract,
    ) -> None:
        if not isinstance(
            contract,
            CommissionContract,
        ):
            raise CommissionContractSnapshotIntegrityError(
                "contract must be CommissionContract."
            )

        if (
            self.tenant_id
            != contract.tenant_id
            or self.commission_id
            != contract.commission_id
            or self.contract_version
            != contract.contract_version
        ):
            raise CommissionContractSnapshotIntegrityError(
                "Snapshot identity does not match contract."
            )

        expected = CommissionContractSnapshot.from_contract(
            contract
        )

        if (
            self.terms_fingerprint
            != expected.terms_fingerprint
        ):
            raise CommissionContractSnapshotIntegrityError(
                "Snapshot terms differ from contract."
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "snapshot_type": (
                "CORE-008.COMMISSION_CONTRACT_SNAPSHOT"
            ),
            "tenant_id": self.tenant_id,
            "commission_id": self.commission_id,
            "contract_version": self.contract_version,
            "terms": dict(self.terms),
            "terms_fingerprint": self.terms_fingerprint,
        }


__all__ = [
    "CommissionContractSnapshotError",
    "CommissionContractSnapshotIntegrityError",
    "CommissionContractSnapshot",
]
