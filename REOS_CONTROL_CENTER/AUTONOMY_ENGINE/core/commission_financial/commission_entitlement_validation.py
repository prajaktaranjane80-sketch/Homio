from __future__ import annotations

from datetime import datetime
from typing import Any

from .commission_calculation import CommissionCalculation
from .commission_entitlement import (
    CommissionEntitlement,
    CommissionEntitlementState,
)
from .commission_contract import CommissionPartyReference


def validate_entitlement(
    entitlement: CommissionEntitlement,
    calculation: CommissionCalculation,
    *,
    at: datetime,
) -> tuple[str, ...]:
    errors: list[str] = []

    if not isinstance(
        entitlement,
        CommissionEntitlement,
    ):
        return ("entitlement must be CommissionEntitlement.",)

    if not isinstance(
        calculation,
        CommissionCalculation,
    ):
        return ("calculation must be CommissionCalculation.",)

    if (
        entitlement.tenant_id
        != calculation.tenant_id
    ):
        errors.append(
            "tenant mismatch"
        )

    if (
        entitlement.commission_id
        != calculation.commission_id
    ):
        errors.append(
            "commission mismatch"
        )

    if (
        entitlement.calculation_id
        != calculation.calculation_id
    ):
        errors.append(
            "calculation mismatch"
        )

    if (
        entitlement.calculation_version
        != calculation.calculation_version
    ):
        errors.append(
            "calculation version mismatch"
        )

    if (
        entitlement.entitled_amount.currency.identity_key
        != calculation.commission_amount.currency.identity_key
    ):
        errors.append(
            "currency mismatch"
        )

    if (
        entitlement.entitled_amount.amount
        > calculation.commission_amount.amount
    ):
        errors.append(
            "entitlement exceeds calculation"
        )

    if (
        entitlement.state
        is CommissionEntitlementState.VOID
    ):
        errors.append(
            "void entitlement cannot be consumed"
        )

    try:
        calculation_time = calculation.calculated_at
        entitlement_time = entitlement.established_at

        if entitlement_time < calculation_time:
            errors.append(
                "entitlement precedes calculation"
            )

    except Exception as exc:
        errors.append(str(exc))

    return tuple(errors)


def entitlement_validation_report(
    entitlement: CommissionEntitlement,
    calculation: CommissionCalculation,
    *,
    at: datetime,
) -> dict[str, Any]:
    errors = validate_entitlement(
        entitlement,
        calculation,
        at=at,
    )

    return {
        "valid": not errors,
        "errors": errors,
        "entitlement_id": (
            entitlement.entitlement_id
            if isinstance(
                entitlement,
                CommissionEntitlement,
            )
            else None
        ),
        "calculation_id": (
            calculation.calculation_id
            if isinstance(
                calculation,
                CommissionCalculation,
            )
            else None
        ),
    }


__all__ = [
    "validate_entitlement",
    "entitlement_validation_report",
]
