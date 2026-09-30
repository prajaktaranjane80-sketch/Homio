from __future__ import annotations

from dataclasses import dataclass

from .commission_contract import (
    CommissionContract,
    CommissionContractState,
)


class CommissionContractValidationResultError(
    ValueError
):
    """Invalid contract validation result."""


@dataclass(frozen=True, slots=True)
class CommissionContractValidationResult:
    """Deterministic validation result.

    This is a contract validator, not another governance engine.
    """

    valid: bool
    errors: tuple[str, ...]
    warnings: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(
            self.valid,
            bool,
        ):
            raise CommissionContractValidationResultError(
                "valid must be boolean."
            )

        errors = tuple(
            str(error).strip()
            for error in self.errors
            if str(error).strip()
        )

        warnings = tuple(
            str(warning).strip()
            for warning in self.warnings
            if str(warning).strip()
        )

        object.__setattr__(
            self,
            "errors",
            errors,
        )

        object.__setattr__(
            self,
            "warnings",
            warnings,
        )

        expected = not errors

        if self.valid != expected:
            raise CommissionContractValidationResultError(
                "valid must equal the absence of errors."
            )

    def to_dict(self) -> dict[str, object]:
        return {
            "valid": self.valid,
            "errors": list(
                self.errors
            ),
            "warnings": list(
                self.warnings
            ),
        }


def validate_commission_contract(
    contract: CommissionContract,
    *,
    expected_tenant_id: str | None = None,
) -> CommissionContractValidationResult:
    """Validate structural CORE-008 T02 contract integrity.

    No calculation or authorization is performed here.
    """

    errors: list[str] = []
    warnings: list[str] = []

    if not isinstance(
        contract,
        CommissionContract,
    ):
        return CommissionContractValidationResult(
            valid=False,
            errors=(
                "contract must be CommissionContract.",
            ),
        )

    if expected_tenant_id is not None:
        if contract.tenant_id != expected_tenant_id:
            errors.append(
                "Contract tenant differs from expected tenant."
            )

    if (
        contract.state
        is CommissionContractState.ACTIVE
        and contract.effective_to is not None
        and contract.effective_to <= contract.effective_from
    ):
        errors.append(
            "ACTIVE contract contains invalid effective window."
        )

    if (
        contract.contract_version < 1
    ):
        errors.append(
            "Contract version must be positive."
        )

    if not contract.provenance.evidence_reference:
        errors.append(
            "Active financial terms require evidence reference."
        )

    if (
        not contract.eligibility_rules
        and contract.state
        is CommissionContractState.ACTIVE
    ):
        warnings.append(
            "Active contract has no explicit eligibility rules."
        )

    if (
        contract.effective_to is None
        and contract.state
        is CommissionContractState.EXPIRED
    ):
        warnings.append(
            "EXPIRED contract has no explicit effective_to."
        )

    return CommissionContractValidationResult(
        valid=not errors,
        errors=tuple(errors),
        warnings=tuple(warnings),
    )


def assert_valid_commission_contract(
    contract: CommissionContract,
    *,
    expected_tenant_id: str | None = None,
) -> None:
    result = validate_commission_contract(
        contract,
        expected_tenant_id=expected_tenant_id,
    )

    if not result.valid:
        raise ValueError(
            "Invalid commission contract: "
            + "; ".join(
                result.errors
            )
        )


__all__ = [
    "CommissionContractValidationResultError",
    "CommissionContractValidationResult",
    "validate_commission_contract",
    "assert_valid_commission_contract",
]
