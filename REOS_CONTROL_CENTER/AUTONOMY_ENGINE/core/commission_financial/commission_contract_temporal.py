from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from .commission_contract import (
    CommissionContract,
    CommissionContractValidationError,
)


class CommissionContractTemporalError(
    ValueError
):
    """Base temporal commission-contract error."""


class CommissionContractTemporalConflictError(
    CommissionContractTemporalError
):
    """Multiple or overlapping effective terms detected."""


@dataclass(frozen=True, slots=True)
class EffectiveCommissionContract:
    """Resolved commission contract at one instant."""

    contract: CommissionContract
    effective_at: datetime

    def __post_init__(self) -> None:
        if not isinstance(
            self.contract,
            CommissionContract,
        ):
            raise CommissionContractTemporalError(
                "contract must be CommissionContract."
            )

        if not isinstance(
            self.effective_at,
            datetime,
        ):
            raise CommissionContractTemporalError(
                "effective_at must be datetime."
            )

        if (
            self.effective_at.tzinfo is None
            or self.effective_at.utcoffset() is None
        ):
            raise CommissionContractTemporalError(
                "effective_at must be timezone-aware."
            )

    def to_dict(self) -> dict[str, object]:
        return {
            "commission_id": self.contract.commission_id,
            "tenant_id": self.contract.tenant_id,
            "contract_version": self.contract.contract_version,
            "effective_at": self.effective_at.isoformat(),
            "terms_fingerprint": (
                self.contract.immutable_terms_fingerprint
            ),
        }


def resolve_effective_contract(
    contracts: tuple[CommissionContract, ...],
    *,
    at: datetime,
) -> EffectiveCommissionContract:
    """Resolve exactly one effective contract.

    No persistence, calculation, governance or authorization occurs here.
    """

    if not contracts:
        raise CommissionContractValidationError(
            "At least one commission contract is required."
        )

    matches = tuple(
        contract
        for contract in contracts
        if contract.is_effective_at(at)
    )

    if len(matches) == 0:
        raise CommissionContractTemporalConflictError(
            "No active commission contract exists at requested time."
        )

    if len(matches) > 1:
        raise CommissionContractTemporalConflictError(
            "Multiple active commission contracts exist at requested time."
        )

    return EffectiveCommissionContract(
        contract=matches[0],
        effective_at=at,
    )


def validate_non_overlapping_terms(
    contracts: tuple[CommissionContract, ...],
) -> None:
    """Validate that contract effective windows do not overlap."""

    ordered = sorted(
        contracts,
        key=lambda value: (
            value.tenant_id,
            value.commission_id,
            value.effective_from,
            value.contract_version,
        ),
    )

    for previous, current in zip(
        ordered,
        ordered[1:],
    ):
        if previous.identity_key != current.identity_key:
            continue

        previous_end = previous.effective_to

        if previous_end is None:
            raise CommissionContractTemporalConflictError(
                "Open-ended commission term cannot be followed "
                "by another version."
            )

        if current.effective_from < previous_end:
            raise CommissionContractTemporalConflictError(
                "Commission contract effective windows overlap."
            )


__all__ = [
    "CommissionContractTemporalError",
    "CommissionContractTemporalConflictError",
    "EffectiveCommissionContract",
    "resolve_effective_contract",
    "validate_non_overlapping_terms",
]
