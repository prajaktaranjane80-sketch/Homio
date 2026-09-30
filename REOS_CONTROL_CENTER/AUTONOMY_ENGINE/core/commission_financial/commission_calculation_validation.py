from __future__ import annotations

from datetime import datetime
from typing import Any

from .commission_calculation import (
    CommissionCalculation,
    CommissionCalculationValidationError,
)
from .commission_calculation_basis import (
    CommissionCalculationBasis,
)
from .commission_contract import (
    CommissionContract,
)


def validate_calculation_inputs(
    contract: CommissionContract,
    basis: CommissionCalculationBasis,
    *,
    calculated_at: datetime,
) -> tuple[str, ...]:
    """Return deterministic validation failures.

    This validator never calculates money and never mutates state.
    """

    errors: list[str] = []

    if not isinstance(
        contract,
        CommissionContract,
    ):
        errors.append(
            "contract must be CommissionContract."
        )

    if not isinstance(
        basis,
        CommissionCalculationBasis,
    ):
        errors.append(
            "basis must be CommissionCalculationBasis."
        )

    if errors:
        return tuple(errors)

    try:
        if not contract.is_effective_at(
            calculated_at
        ):
            errors.append(
                "commission contract is not ACTIVE "
                "at calculation time"
            )
    except Exception as exc:
        errors.append(str(exc))

    if (
        basis.source_reference
        != contract.basis.source_reference
    ):
        errors.append(
            "basis source_reference mismatch"
        )

    if (
        basis.basis_code
        != contract.basis.basis_type.value
    ):
        errors.append(
            "basis_code mismatch"
        )

    if contract.rate.rate_type.value == "FIXED_AMOUNT":
        if contract.rate.currency is None:
            errors.append(
                "fixed commission contract has no currency"
            )
        elif (
            contract.rate.currency.identity_key
            != basis.amount.currency.identity_key
        ):
            errors.append(
                "fixed commission currency mismatch"
            )

    return tuple(errors)


def assert_valid_calculation(
    calculation: CommissionCalculation,
) -> None:
    if not isinstance(
        calculation,
        CommissionCalculation,
    ):
        raise CommissionCalculationValidationError(
            "calculation must be CommissionCalculation."
        )

    if calculation.commission_amount.amount < 0:
        raise CommissionCalculationValidationError(
            "commission_amount cannot be negative."
        )

    if not calculation.idempotency_key.strip():
        raise CommissionCalculationValidationError(
            "idempotency_key must be populated."
        )

    if calculation.basis_reference.strip() == "":
        raise CommissionCalculationValidationError(
            "basis_reference must be populated."
        )


def calculation_validation_report(
    calculation: CommissionCalculation,
) -> dict[str, Any]:
    try:
        assert_valid_calculation(
            calculation
        )
    except CommissionCalculationValidationError as exc:
        return {
            "valid": False,
            "errors": (str(exc),),
        }

    return {
        "valid": True,
        "errors": (),
    }


__all__ = [
    "validate_calculation_inputs",
    "assert_valid_calculation",
    "calculation_validation_report",
]
