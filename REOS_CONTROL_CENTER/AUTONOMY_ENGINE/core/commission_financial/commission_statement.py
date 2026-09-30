from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Any, Mapping
from uuid import uuid4

from ..contract_primitives import deep_freeze, fingerprint
from .commission_adjustment import CommissionAdjustment
from .commission_invoice import CommissionInvoice
from .commission_reconciliation import CommissionReconciliation
from .commission_settlement import CommissionSettlement
from .commission_tax import CommissionTaxAssessment
from .financial_domain import (
    FinancialCurrencyMismatchError,
    FinancialTenantScopeError,
    MonetaryAmount,
)


CORE008_COMMISSION_STATEMENT_SCHEMA_VERSION = 1


class CommissionStatementError(ValueError):
    """Base financial statement error."""


class CommissionStatementValidationError(
    CommissionStatementError
):
    """Invalid financial statement."""


class CommissionStatementState(str, Enum):
    DRAFT = "DRAFT"
    ISSUED = "ISSUED"
    FINAL = "FINAL"
    SUPERSEDED = "SUPERSEDED"
    VOID = "VOID"


def _text(
    value: str,
    field: str,
) -> str:
    if not isinstance(value, str) or not value.strip():
        raise CommissionStatementValidationError(
            f"{field} must be non-empty text."
        )
    return value.strip()


def _aware(
    value: datetime,
    field: str,
) -> datetime:
    if (
        not isinstance(value, datetime)
        or value.tzinfo is None
        or value.utcoffset() is None
    ):
        raise CommissionStatementValidationError(
            f"{field} must be timezone-aware."
        )
    return value.astimezone(timezone.utc)


def _positive(
    value: int,
    field: str,
) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or value < 1
    ):
        raise CommissionStatementValidationError(
            f"{field} must be a positive integer."
        )
    return value


@dataclass(frozen=True, slots=True)
class CommissionStatement:
    """Immutable consolidated commission financial statement."""

    statement_id: str
    tenant_id: str
    commission_id: str
    statement_version: int

    gross_commission: MonetaryAmount
    total_adjustments: MonetaryAmount
    invoiced_amount: MonetaryAmount
    settled_amount: MonetaryAmount
    reconciled_amount: MonetaryAmount
    total_tax: MonetaryAmount
    total_withholding: MonetaryAmount

    outstanding_amount: MonetaryAmount
    unresolved_variance: MonetaryAmount

    source_invoice_ids: tuple[str, ...]
    source_settlement_ids: tuple[str, ...]
    source_reconciliation_ids: tuple[str, ...]
    source_adjustment_ids: tuple[str, ...]
    source_tax_assessment_ids: tuple[str, ...]

    generated_at: datetime
    provenance_reference: str
    authorization_reference: str
    state: CommissionStatementState = (
        CommissionStatementState.DRAFT
    )
    metadata: Mapping[str, Any] = ()

    def __post_init__(self) -> None:
        for field in (
            "statement_id",
            "tenant_id",
            "commission_id",
            "provenance_reference",
            "authorization_reference",
        ):
            object.__setattr__(
                self,
                field,
                _text(
                    getattr(self, field),
                    field,
                ),
            )

        object.__setattr__(
            self,
            "statement_version",
            _positive(
                self.statement_version,
                "statement_version",
            ),
        )

        monetary_fields = (
            "gross_commission",
            "total_adjustments",
            "invoiced_amount",
            "settled_amount",
            "reconciled_amount",
            "total_tax",
            "total_withholding",
            "outstanding_amount",
            "unresolved_variance",
        )

        for field in monetary_fields:
            value = getattr(self, field)
            if not isinstance(
                value,
                MonetaryAmount,
            ):
                raise CommissionStatementValidationError(
                    f"{field} must be MonetaryAmount."
                )

        currencies = {
            getattr(
                self,
                field,
            ).currency.identity_key
            for field in monetary_fields
        }

        if len(currencies) != 1:
            raise FinancialCurrencyMismatchError(
                "All statement monetary values must "
                "use identical currency semantics."
            )

        expected_outstanding = (
            self.invoiced_amount.amount
            + self.total_adjustments.amount
            - self.settled_amount.amount
        )

        if (
            expected_outstanding
            != self.outstanding_amount.amount
        ):
            raise CommissionStatementValidationError(
                "outstanding_amount does not match "
                "statement inputs."
            )

        expected_unresolved_variance = (
            self.settled_amount.amount
            - self.reconciled_amount.amount
        )

        if (
            expected_unresolved_variance
            != self.unresolved_variance.amount
        ):
            raise CommissionStatementValidationError(
                "unresolved_variance does not match "
                "settled minus reconciled."
            )

        object.__setattr__(
            self,
            "source_invoice_ids",
            self._normalize_ids(
                self.source_invoice_ids,
                "source_invoice_ids",
            ),
        )
        object.__setattr__(
            self,
            "source_settlement_ids",
            self._normalize_ids(
                self.source_settlement_ids,
                "source_settlement_ids",
            ),
        )
        object.__setattr__(
            self,
            "source_reconciliation_ids",
            self._normalize_ids(
                self.source_reconciliation_ids,
                "source_reconciliation_ids",
            ),
        )
        object.__setattr__(
            self,
            "source_adjustment_ids",
            self._normalize_ids(
                self.source_adjustment_ids,
                "source_adjustment_ids",
            ),
        )
        object.__setattr__(
            self,
            "source_tax_assessment_ids",
            self._normalize_ids(
                self.source_tax_assessment_ids,
                "source_tax_assessment_ids",
            ),
        )

        object.__setattr__(
            self,
            "generated_at",
            _aware(
                self.generated_at,
                "generated_at",
            ),
        )

        try:
            state = CommissionStatementState(
                self.state
            )
        except ValueError as exc:
            raise CommissionStatementValidationError(
                "Unsupported statement state."
            ) from exc

        object.__setattr__(
            self,
            "state",
            state,
        )

        metadata = (
            {}
            if self.metadata == ()
            else self.metadata
        )

        if not isinstance(
            metadata,
            Mapping,
        ):
            raise CommissionStatementValidationError(
                "metadata must be a mapping."
            )

        object.__setattr__(
            self,
            "metadata",
            deep_freeze(
                dict(metadata),
                field_name="metadata",
            ),
        )

    @staticmethod
    def _normalize_ids(
        values: tuple[str, ...],
        field: str,
    ) -> tuple[str, ...]:
        normalized = tuple(values)

        if any(
            not isinstance(
                value,
                str,
            )
            or not value.strip()
            for value in normalized
        ):
            raise CommissionStatementValidationError(
                f"{field} contains invalid identifiers."
            )

        if len(normalized) != len(set(normalized)):
            raise CommissionStatementValidationError(
                f"{field} contains duplicates."
            )

        return tuple(
            value.strip()
            for value in normalized
        )

    @classmethod
    def build(
        cls,
        *,
        tenant_id: str,
        commission_id: str,
        generated_at: datetime,
        provenance_reference: str,
        authorization_reference: str,
        invoices: tuple[
            CommissionInvoice,
            ...] = (),
        settlements: tuple[
            CommissionSettlement,
            ...] = (),
        reconciliations: tuple[
            CommissionReconciliation,
            ...] = (),
        adjustments: tuple[
            CommissionAdjustment,
            ...] = (),
        tax_assessments: tuple[
            CommissionTaxAssessment,
            ...] = (),
        statement_id: str | None = None,
        statement_version: int = 1,
        state: CommissionStatementState = (
            CommissionStatementState.DRAFT
        ),
        metadata: Mapping[str, Any] | None = None,
    ) -> "CommissionStatement":
        tenant_id = _text(
            tenant_id,
            "tenant_id",
        )
        commission_id = _text(
            commission_id,
            "commission_id",
        )

        invoice_items = tuple(invoices)
        settlement_items = tuple(settlements)
        reconciliation_items = tuple(
            reconciliations
        )
        adjustment_items = tuple(adjustments)
        tax_items = tuple(tax_assessments)

        for item in invoice_items:
            if not isinstance(
                item,
                CommissionInvoice,
            ):
                raise CommissionStatementValidationError(
                    "Invalid invoice input."
                )
            if (
                item.tenant_id != tenant_id
                or item.commission_id != commission_id
            ):
                raise CommissionStatementValidationError(
                    "Invoice is outside statement scope."
                )

        for item in settlement_items:
            if not isinstance(
                item,
                CommissionSettlement,
            ):
                raise CommissionStatementValidationError(
                    "Invalid settlement input."
                )
            if (
                item.tenant_id != tenant_id
                or item.commission_id != commission_id
            ):
                raise CommissionStatementValidationError(
                    "Settlement is outside statement scope."
                )

        for item in reconciliation_items:
            if not isinstance(
                item,
                CommissionReconciliation,
            ):
                raise CommissionStatementValidationError(
                    "Invalid reconciliation input."
                )
            if (
                item.tenant_id != tenant_id
                or item.commission_id != commission_id
            ):
                raise CommissionStatementValidationError(
                    "Reconciliation is outside statement scope."
                )

        for item in adjustment_items:
            if not isinstance(
                item,
                CommissionAdjustment,
            ):
                raise CommissionStatementValidationError(
                    "Invalid adjustment input."
                )
            if (
                item.tenant_id != tenant_id
                or item.commission_id != commission_id
            ):
                raise CommissionStatementValidationError(
                    "Adjustment is outside statement scope."
                )

        for item in tax_items:
            if not isinstance(
                item,
                CommissionTaxAssessment,
            ):
                raise CommissionStatementValidationError(
                    "Invalid tax assessment input."
                )
            if (
                item.tenant_id != tenant_id
                or item.commission_id != commission_id
            ):
                raise CommissionStatementValidationError(
                    "Tax assessment is outside statement scope."
                )

        monetary_candidates: list[MonetaryAmount] = []

        for item in invoice_items:
            monetary_candidates.append(
                item.total_due
            )

        for item in settlement_items:
            monetary_candidates.append(
                item.amount
            )

        for item in adjustment_items:
            monetary_candidates.append(
                item.amount
            )

        for item in tax_items:
            monetary_candidates.append(
                item.total_tax
            )

        if not monetary_candidates:
            raise CommissionStatementValidationError(
                "At least one financial source is required."
            )

        currency_keys = {
            item.currency.identity_key
            for item in monetary_candidates
        }

        if len(currency_keys) != 1:
            raise FinancialCurrencyMismatchError(
                "Statement sources use incompatible currencies."
            )

        currency = monetary_candidates[0].currency

        gross_commission = MonetaryAmount.zero(
            currency
        )

        total_adjustments = MonetaryAmount.zero(
            currency
        )

        invoiced_amount = MonetaryAmount.zero(
            currency
        )

        settled_amount = MonetaryAmount.zero(
            currency
        )

        reconciled_amount = MonetaryAmount.zero(
            currency
        )

        total_tax = MonetaryAmount.zero(
            currency
        )

        total_withholding = MonetaryAmount.zero(
            currency
        )

        for invoice in invoice_items:
            invoiced_amount = invoiced_amount.add(
                invoice.total_due
            )
            gross_commission = (
                gross_commission.add(
                    invoice.subtotal
                )
            )

        for adjustment in adjustment_items:
            sign = Decimal("1")

            if adjustment.adjustment_type.value in (
                "CREDIT",
                "REVERSAL",
            ):
                sign = Decimal("-1")

            total_adjustments = (
                total_adjustments.add(
                    MonetaryAmount.create(
                        adjustment.amount.amount
                        * sign,
                        currency,
                    )
                )
            )

        for settlement in settlement_items:
            settled_amount = settled_amount.add(
                settlement.amount
            )

        for reconciliation in reconciliation_items:
            reconciled_amount = (
                reconciled_amount.add(
                    reconciliation.observed_amount
                )
            )

        for assessment in tax_items:
            total_tax = total_tax.add(
                assessment.total_tax
            )
            total_withholding = (
                total_withholding.add(
                    assessment.total_withholding
                )
            )

        outstanding_amount = (
            invoiced_amount.amount
            + total_adjustments.amount
            - settled_amount.amount
        )

        unresolved_variance = (
            settled_amount.amount
            - reconciled_amount.amount
        )

        return cls(
            statement_id=(
                statement_id
                or str(uuid4())
            ),
            tenant_id=tenant_id,
            commission_id=commission_id,
            statement_version=statement_version,
            gross_commission=gross_commission,
            total_adjustments=total_adjustments,
            invoiced_amount=invoiced_amount,
            settled_amount=settled_amount,
            reconciled_amount=reconciled_amount,
            total_tax=total_tax,
            total_withholding=total_withholding,
            outstanding_amount=MonetaryAmount.create(
                outstanding_amount,
                currency,
            ),
            unresolved_variance=MonetaryAmount.create(
                unresolved_variance,
                currency,
            ),
            source_invoice_ids=tuple(
                item.invoice_id
                for item in invoice_items
            ),
            source_settlement_ids=tuple(
                item.settlement_id
                for item in settlement_items
            ),
            source_reconciliation_ids=tuple(
                item.reconciliation_id
                for item in reconciliation_items
            ),
            source_adjustment_ids=tuple(
                item.adjustment_id
                for item in adjustment_items
            ),
            source_tax_assessment_ids=tuple(
                item.assessment_id
                for item in tax_items
            ),
            generated_at=generated_at,
            provenance_reference=provenance_reference,
            authorization_reference=authorization_reference,
            state=state,
            metadata=(
                {}
                if metadata is None
                else metadata
            ),
        )

    @property
    def identity_key(
        self,
    ) -> tuple[str, str, int]:
        return (
            self.tenant_id,
            self.statement_id,
            self.statement_version,
        )

    @property
    def immutable_fingerprint(self) -> str:
        return fingerprint(
            self.to_dict(
                include_fingerprint=False
            )
        )

    def assert_tenant(
        self,
        tenant_id: str,
    ) -> None:
        tenant_id = _text(
            tenant_id,
            "tenant_id",
        )

        if tenant_id != self.tenant_id:
            raise FinancialTenantScopeError(
                "Financial statement crossed tenant scope."
            )

    def to_dict(
        self,
        *,
        include_fingerprint: bool = True,
    ) -> dict[str, Any]:
        result = {
            "source_of_truth": (
                "CORE-008.COMMISSION_STATEMENT"
            ),
            "schema_version": (
                CORE008_COMMISSION_STATEMENT_SCHEMA_VERSION
            ),
            "statement_id": self.statement_id,
            "tenant_id": self.tenant_id,
            "commission_id": self.commission_id,
            "statement_version": (
                self.statement_version
            ),
            "gross_commission": (
                self.gross_commission.to_dict()
            ),
            "total_adjustments": (
                self.total_adjustments.to_dict()
            ),
            "invoiced_amount": (
                self.invoiced_amount.to_dict()
            ),
            "settled_amount": (
                self.settled_amount.to_dict()
            ),
            "reconciled_amount": (
                self.reconciled_amount.to_dict()
            ),
            "total_tax": (
                self.total_tax.to_dict()
            ),
            "total_withholding": (
                self.total_withholding.to_dict()
            ),
            "outstanding_amount": (
                self.outstanding_amount.to_dict()
            ),
            "unresolved_variance": (
                self.unresolved_variance.to_dict()
            ),
            "source_invoice_ids": list(
                self.source_invoice_ids
            ),
            "source_settlement_ids": list(
                self.source_settlement_ids
            ),
            "source_reconciliation_ids": list(
                self.source_reconciliation_ids
            ),
            "source_adjustment_ids": list(
                self.source_adjustment_ids
            ),
            "source_tax_assessment_ids": list(
                self.source_tax_assessment_ids
            ),
            "generated_at": (
                self.generated_at.isoformat()
            ),
            "provenance_reference": (
                self.provenance_reference
            ),
            "authorization_reference": (
                self.authorization_reference
            ),
            "state": self.state.value,
            "metadata": dict(self.metadata),
        }

        if include_fingerprint:
            result["immutable_fingerprint"] = (
                self.immutable_fingerprint
            )

        return result


__all__ = [
    "CORE008_COMMISSION_STATEMENT_SCHEMA_VERSION",
    "CommissionStatementError",
    "CommissionStatementValidationError",
    "CommissionStatementState",
    "CommissionStatement",
]
