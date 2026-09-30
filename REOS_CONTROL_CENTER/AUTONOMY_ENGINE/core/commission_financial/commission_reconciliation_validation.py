from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from .commission_reconciliation import (
    CommissionExternalSettlementEvidence,
    CommissionReconciliation,
)
from .commission_settlement import CommissionSettlement


def validate_reconciliation(
    reconciliation: CommissionReconciliation,
    settlement: CommissionSettlement,
    evidence: CommissionExternalSettlementEvidence,
    *,
    at: datetime,
) -> tuple[str, ...]:
    errors: list[str] = []

    if not isinstance(
        reconciliation,
        CommissionReconciliation,
    ):
        return (
            "reconciliation must be CommissionReconciliation.",
        )

    if not isinstance(
        settlement,
        CommissionSettlement,
    ):
        return (
            "settlement must be CommissionSettlement.",
        )

    if not isinstance(
        evidence,
        CommissionExternalSettlementEvidence,
    ):
        return (
            "evidence must be "
            "CommissionExternalSettlementEvidence.",
        )

    if reconciliation.tenant_id != settlement.tenant_id:
        errors.append("tenant mismatch with settlement")

    if reconciliation.tenant_id != evidence.tenant_id:
        errors.append("tenant mismatch with evidence")

    if (
        reconciliation.settlement_id
        != settlement.settlement_id
    ):
        errors.append("settlement identity mismatch")

    if (
        reconciliation.external_evidence_id
        != evidence.evidence_id
    ):
        errors.append("evidence identity mismatch")

    if (
        reconciliation.expected_amount.amount
        != settlement.amount.amount
    ):
        errors.append("expected amount mismatch")

    if (
        reconciliation.observed_amount.amount
        != evidence.observed_amount.amount
    ):
        errors.append("observed amount mismatch")

    expected_variance = (
        evidence.observed_amount.amount
        - settlement.amount.amount
    )

    if (
        reconciliation.variance_amount.amount
        != expected_variance
    ):
        errors.append("variance calculation mismatch")

    if reconciliation.reconciled_at > at:
        errors.append(
            "reconciliation cannot occur after validation time"
        )

    if (
        reconciliation.variance_tolerance.amount
        < Decimal("0")
    ):
        errors.append(
            "variance tolerance cannot be negative"
        )

    return tuple(errors)


def reconciliation_validation_report(
    reconciliation: CommissionReconciliation,
    settlement: CommissionSettlement,
    evidence: CommissionExternalSettlementEvidence,
    *,
    at: datetime,
) -> dict[str, Any]:
    errors = validate_reconciliation(
        reconciliation,
        settlement,
        evidence,
        at=at,
    )

    return {
        "valid": not errors,
        "errors": errors,
    }


__all__ = [
    "validate_reconciliation",
    "reconciliation_validation_report",
]
