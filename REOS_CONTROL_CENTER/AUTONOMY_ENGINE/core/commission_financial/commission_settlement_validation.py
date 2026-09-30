from __future__ import annotations

from datetime import datetime
from typing import Any

from .commission_allocation import CommissionAllocation
from .commission_settlement import (
    CommissionSettlement,
    CommissionSettlementState,
)


def validate_settlement(
    settlement: CommissionSettlement,
    allocation: CommissionAllocation,
    *,
    at: datetime,
) -> tuple[str, ...]:
    errors: list[str] = []

    if not isinstance(
        settlement,
        CommissionSettlement,
    ):
        return (
            "settlement must be CommissionSettlement.",
        )

    if not isinstance(
        allocation,
        CommissionAllocation,
    ):
        return (
            "allocation must be CommissionAllocation.",
        )

    if settlement.tenant_id != allocation.tenant_id:
        errors.append("tenant mismatch")

    if (
        settlement.commission_id
        != allocation.commission_id
    ):
        errors.append("commission mismatch")

    if (
        settlement.allocation_set_id
        != allocation.allocation_set_id
    ):
        errors.append("allocation mismatch")

    if (
        settlement.amount.currency.identity_key
        != allocation.total_amount.currency.identity_key
    ):
        errors.append("currency mismatch")

    if (
        settlement.amount.amount
        > allocation.total_amount.amount
    ):
        errors.append(
            "settlement exceeds allocation"
        )

    if settlement.state is CommissionSettlementState.FAILED:
        if not settlement.failure_code:
            errors.append(
                "failed settlement requires failure_code"
            )

    if settlement.requested_at > allocation.lines[0].amount.currency.rounding_mode if False else False:
        errors.append("invalid temporal relationship")

    if settlement.requested_at < at.replace(
        microsecond=0
    ):
        pass

    return tuple(errors)


def settlement_validation_report(
    settlement: CommissionSettlement,
    allocation: CommissionAllocation,
    *,
    at: datetime,
) -> dict[str, Any]:
    errors = validate_settlement(
        settlement,
        allocation,
        at=at,
    )

    return {
        "valid": not errors,
        "errors": errors,
    }


__all__ = [
    "validate_settlement",
    "settlement_validation_report",
]
