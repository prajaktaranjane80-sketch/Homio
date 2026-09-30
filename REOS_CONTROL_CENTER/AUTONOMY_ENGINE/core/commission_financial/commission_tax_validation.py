from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from .commission_invoice import CommissionInvoice
from .commission_tax import (
    CommissionTaxAssessment,
    CommissionTaxComponent,
    CommissionTaxComponentType,
)


def validate_tax_assessment(
    assessment: CommissionTaxAssessment,
    invoice: CommissionInvoice,
    *,
    at: datetime,
) -> tuple[str, ...]:
    errors: list[str] = []

    if not isinstance(
        assessment,
        CommissionTaxAssessment,
    ):
        return (
            "assessment must be CommissionTaxAssessment.",
        )

    if not isinstance(
        invoice,
        CommissionInvoice,
    ):
        return (
            "invoice must be CommissionInvoice.",
        )

    if assessment.tenant_id != invoice.tenant_id:
        errors.append("tenant mismatch")

    if assessment.commission_id != invoice.commission_id:
        errors.append("commission mismatch")

    if assessment.invoice_id != invoice.invoice_id:
        errors.append("invoice mismatch")

    if (
        assessment.taxable_base.currency.identity_key
        != invoice.total_due.currency.identity_key
    ):
        errors.append("taxable base currency mismatch")

    if (
        assessment.taxable_base.amount
        > invoice.total_due.amount
    ):
        errors.append(
            "taxable base exceeds invoice total"
        )

    if assessment.assessed_at > at:
        errors.append(
            "assessment cannot be dated after validation time"
        )

    for component in (
        assessment.tax_components
        + assessment.withholding_components
    ):
        if not isinstance(
            component,
            CommissionTaxComponent,
        ):
            errors.append(
                "assessment contains invalid component"
            )
            continue

        if (
            component.base_amount.amount
            > assessment.taxable_base.amount
        ):
            errors.append(
                "tax component base exceeds taxable base"
            )

        if (
            component.amount.amount
            != (
                component.base_amount.amount
                * component.rate_percent
                / Decimal("100")
            ).quantize(
                component.amount.currency.quantum
            )
        ):
            errors.append(
                "tax component amount is not "
                "deterministic from its declared rate"
            )

    for component in assessment.tax_components:
        if (
            component.component_type
            is not CommissionTaxComponentType.TAX
        ):
            errors.append(
                "tax_components contains non-TAX component"
            )

    for component in assessment.withholding_components:
        if (
            component.component_type
            is not CommissionTaxComponentType.WITHHOLDING
        ):
            errors.append(
                "withholding_components contains "
                "non-WITHHOLDING component"
            )

    return tuple(errors)


def tax_validation_report(
    assessment: CommissionTaxAssessment,
    invoice: CommissionInvoice,
    *,
    at: datetime,
) -> dict[str, Any]:
    errors = validate_tax_assessment(
        assessment,
        invoice,
        at=at,
    )

    return {
        "valid": not errors,
        "errors": errors,
    }


__all__ = [
    "validate_tax_assessment",
    "tax_validation_report",
]
