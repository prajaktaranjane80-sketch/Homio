from __future__ import annotations

from decimal import Decimal
from typing import Any

from .commission_allocation import (
    CommissionAllocation,
)
from .commission_calculation import (
    CommissionCalculation,
)


def validate_allocation(
    allocation: CommissionAllocation,
    calculation: CommissionCalculation,
) -> tuple[str, ...]:
    errors: list[str] = []

    if not isinstance(
        allocation,
        CommissionAllocation,
    ):
        return ("allocation must be CommissionAllocation.",)

    if not isinstance(
        calculation,
        CommissionCalculation,
    ):
        return ("calculation must be CommissionCalculation.",)

    if (
        allocation.tenant_id
        != calculation.tenant_id
    ):
        errors.append(
            "tenant mismatch"
        )

    if (
        allocation.commission_id
        != calculation.commission_id
    ):
        errors.append(
            "commission mismatch"
        )

    if (
        allocation.calculation_id
        != calculation.calculation_id
    ):
        errors.append(
            "calculation mismatch"
        )

    if (
        allocation.calculation_version
        != calculation.calculation_version
    ):
        errors.append(
            "calculation version mismatch"
        )

    if (
        allocation.total_amount.amount
        != calculation.commission_amount.amount
    ):
        errors.append(
            "allocation total does not equal "
            "calculated commission"
        )

    if (
        allocation.total_amount.currency.identity_key
        != calculation.commission_amount.currency.identity_key
    ):
        errors.append(
            "allocation currency mismatch"
        )

    line_sum = sum(
        (
            line.amount.amount
            for line in allocation.lines
        ),
        Decimal("0"),
    )

    if line_sum != allocation.total_amount.amount:
        errors.append(
            "allocation lines do not equal total"
        )

    ratio_sum = sum(
        (
            line.allocation_ratio
            for line in allocation.lines
        ),
        Decimal("0"),
    )

    if (
        allocation.total_amount.amount != 0
        and ratio_sum != Decimal("100")
    ):
        errors.append(
            "allocation ratios do not equal 100"
        )

    return tuple(errors)


def allocation_validation_report(
    allocation: CommissionAllocation,
    calculation: CommissionCalculation,
) -> dict[str, Any]:
    errors = validate_allocation(
        allocation,
        calculation,
    )

    return {
        "valid": not errors,
        "errors": errors,
    }


__all__ = [
    "validate_allocation",
    "allocation_validation_report",
]
