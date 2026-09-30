from __future__ import annotations

from dataclasses import dataclass

from .commission_contract import (
    CommissionContract,
    CommissionContractState,
)
from .commission_contract_snapshot import (
    CommissionContractSnapshot,
)


@dataclass(frozen=True, slots=True)
class CommissionContractIntegrityReport:
    """Deterministic structural integrity result."""

    valid: bool
    errors: tuple[str, ...]
    warnings: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "errors",
            tuple(
                item.strip()
                for item in self.errors
                if item.strip()
            ),
        )

        object.__setattr__(
            self,
            "warnings",
            tuple(
                item.strip()
                for item in self.warnings
                if item.strip()
            ),
        )

        expected = not self.errors

        if self.valid != expected:
            raise ValueError(
                "valid must equal absence of errors."
            )

    def to_dict(self) -> dict[str, object]:
        return {
            "valid": self.valid,
            "errors": list(self.errors),
            "warnings": list(self.warnings),
        }


def inspect_commission_contract_integrity(
    contract: CommissionContract,
) -> CommissionContractIntegrityReport:
    """Perform T02 structural integrity checks only.

    No business decision, calculation, authorization,
    governance or settlement decision is made.
    """

    errors: list[str] = []
    warnings: list[str] = []

    if not isinstance(
        contract,
        CommissionContract,
    ):
        return CommissionContractIntegrityReport(
            valid=False,
            errors=(
                "contract must be CommissionContract.",
            ),
            warnings=(),
        )

    if not contract.tenant_id.strip():
        errors.append(
            "Tenant identity is empty."
        )

    if not contract.commission_id.strip():
        errors.append(
            "Commission identity is empty."
        )

    if contract.contract_version < 1:
        errors.append(
            "Contract version must be positive."
        )

    if (
        contract.effective_to is not None
        and contract.effective_to
        <= contract.effective_from
    ):
        errors.append(
            "Effective date window is invalid."
        )

    snapshot = CommissionContractSnapshot.from_contract(
        contract
    )

    if (
        snapshot.terms_fingerprint
        != contract.immutable_terms_fingerprint
    ):
        errors.append(
            "Contract fingerprint and snapshot fingerprint differ."
        )

    if (
        contract.state
        is CommissionContractState.ACTIVE
        and not contract.provenance.evidence_reference.strip()
    ):
        errors.append(
            "ACTIVE contract has no provenance evidence."
        )

    if (
        contract.state
        is CommissionContractState.ACTIVE
        and not contract.eligibility_rules
    ):
        warnings.append(
            "ACTIVE contract has no explicit eligibility rules."
        )

    if (
        contract.rate.rate_type.value
        == "PERCENTAGE"
        and contract.rate.value == 0
    ):
        warnings.append(
            "Commission percentage is zero."
        )

    return CommissionContractIntegrityReport(
        valid=not errors,
        errors=tuple(errors),
        warnings=tuple(warnings),
    )


def assert_commission_contract_integrity(
    contract: CommissionContract,
) -> None:
    report = inspect_commission_contract_integrity(
        contract
    )

    if not report.valid:
        raise ValueError(
            "Commission contract integrity failure: "
            + "; ".join(report.errors)
        )


__all__ = [
    "CommissionContractIntegrityReport",
    "inspect_commission_contract_integrity",
    "assert_commission_contract_integrity",
]
