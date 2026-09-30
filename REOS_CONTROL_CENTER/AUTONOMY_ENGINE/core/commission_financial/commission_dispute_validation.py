from __future__ import annotations

from typing import Any

from .commission_dispute import (
    CommissionDispute,
    CommissionDisputeResolution,
    CommissionDisputeState,
)
from .commission_settlement import CommissionSettlement


def validate_dispute(
    dispute: CommissionDispute,
    settlement: CommissionSettlement,
) -> tuple[str, ...]:
    errors: list[str] = []

    if not isinstance(
        dispute,
        CommissionDispute,
    ):
        return ("dispute must be CommissionDispute.",)

    if not isinstance(
        settlement,
        CommissionSettlement,
    ):
        return (
            "settlement must be CommissionSettlement.",
        )

    if dispute.tenant_id != settlement.tenant_id:
        errors.append("tenant mismatch")

    if dispute.commission_id != settlement.commission_id:
        errors.append("commission mismatch")

    if dispute.settlement_id != settlement.settlement_id:
        errors.append("settlement mismatch")

    if (
        dispute.disputed_amount is not None
        and dispute.disputed_amount.currency.identity_key
        != settlement.amount.currency.identity_key
    ):
        errors.append("disputed amount currency mismatch")

    if (
        dispute.disputed_amount is not None
        and dispute.disputed_amount.amount
        > settlement.amount.amount
    ):
        errors.append(
            "disputed amount exceeds settlement"
        )

    if (
        dispute.state
        is CommissionDisputeState.RESOLVED
        and dispute.resolution
        is CommissionDisputeResolution.NONE
    ):
        errors.append(
            "resolved dispute requires resolution"
        )

    if (
        dispute.resolution
        is not CommissionDisputeResolution.NONE
        and not dispute.resolution_reference
    ):
        errors.append(
            "resolution requires resolution_reference"
        )

    return tuple(errors)


def dispute_validation_report(
    dispute: CommissionDispute,
    settlement: CommissionSettlement,
) -> dict[str, Any]:
    errors = validate_dispute(
        dispute,
        settlement,
    )

    return {
        "valid": not errors,
        "errors": errors,
    }


__all__ = [
    "validate_dispute",
    "dispute_validation_report",
]
