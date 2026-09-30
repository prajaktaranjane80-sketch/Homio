from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Any, Mapping
from uuid import uuid4

from ..contract_primitives import deep_freeze, fingerprint
from .commission_allocation import CommissionAllocation
from .commission_adjustment import CommissionAdjustment
from .commission_settlement import CommissionSettlement
from .financial_domain import (
    FinancialCurrencyMismatchError,
    FinancialTenantScopeError,
    MonetaryAmount,
)


CORE008_COMMISSION_INVOICE_SCHEMA_VERSION = 1


class CommissionInvoiceError(ValueError):
    """Base commission invoice error."""


class CommissionInvoiceValidationError(
    CommissionInvoiceError
):
    """Invalid commission invoice."""


class CommissionInvoiceState(str, Enum):
    DRAFT = "DRAFT"
    ISSUED = "ISSUED"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    PARTIALLY_PAID = "PARTIALLY_PAID"
    PAID = "PAID"
    OVERDUE = "OVERDUE"
    VOID = "VOID"
    DISPUTED = "DISPUTED"


class CommissionInvoiceLineType(str, Enum):
    COMMISSION = "COMMISSION"
    ADJUSTMENT_CREDIT = "ADJUSTMENT_CREDIT"
    ADJUSTMENT_DEBIT = "ADJUSTMENT_DEBIT"
    OTHER = "OTHER"


def _text(
    value: str,
    field: str,
) -> str:
    if not isinstance(value, str) or not value.strip():
        raise CommissionInvoiceValidationError(
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
        raise CommissionInvoiceValidationError(
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
        raise CommissionInvoiceValidationError(
            f"{field} must be a positive integer."
        )

    return value


@dataclass(frozen=True, slots=True)
class CommissionInvoiceLine:
    """Immutable invoice line."""

    line_id: str
    line_type: CommissionInvoiceLineType
    description: str
    reference_id: str
    amount: MonetaryAmount
    sequence: int
    metadata: Mapping[str, Any] = ()

    def __post_init__(self) -> None:
        for field in (
            "line_id",
            "description",
            "reference_id",
        ):
            object.__setattr__(
                self,
                field,
                _text(
                    getattr(self, field),
                    field,
                ),
            )

        try:
            line_type = CommissionInvoiceLineType(
                self.line_type
            )
        except ValueError as exc:
            raise CommissionInvoiceValidationError(
                "Unsupported invoice line type."
            ) from exc

        object.__setattr__(
            self,
            "line_type",
            line_type,
        )

        if not isinstance(
            self.amount,
            MonetaryAmount,
        ):
            raise CommissionInvoiceValidationError(
                "amount must be MonetaryAmount."
            )

        if (
            isinstance(self.sequence, bool)
            or not isinstance(self.sequence, int)
            or self.sequence < 1
        ):
            raise CommissionInvoiceValidationError(
                "sequence must be a positive integer."
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
            raise CommissionInvoiceValidationError(
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

    def to_dict(self) -> dict[str, Any]:
        return {
            "line_id": self.line_id,
            "line_type": self.line_type.value,
            "description": self.description,
            "reference_id": self.reference_id,
            "amount": self.amount.to_dict(),
            "sequence": self.sequence,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class CommissionInvoice:
    """Immutable commission invoice / financial obligation.

    This object records an invoice obligation.
    It does not execute payment or post a ledger entry.
    """

    invoice_id: str
    tenant_id: str
    commission_id: str
    allocation_set_id: str
    settlement_id: str
    invoice_version: int
    invoice_number: str
    issuer_reference: str
    payer_reference: str
    payee_reference: str
    currency_code: str
    lines: tuple[CommissionInvoiceLine, ...]
    subtotal: MonetaryAmount
    adjustment_total: MonetaryAmount
    total_due: MonetaryAmount
    issued_at: datetime
    due_at: datetime
    state: CommissionInvoiceState
    authorization_reference: str
    provenance_reference: str
    external_invoice_reference: str | None = None
    metadata: Mapping[str, Any] = ()

    def __post_init__(self) -> None:
        for field in (
            "invoice_id",
            "tenant_id",
            "commission_id",
            "allocation_set_id",
            "settlement_id",
            "invoice_number",
            "issuer_reference",
            "payer_reference",
            "payee_reference",
            "currency_code",
            "authorization_reference",
            "provenance_reference",
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
            "invoice_version",
            _positive(
                self.invoice_version,
                "invoice_version",
            ),
        )

        lines = tuple(self.lines)

        if not lines:
            raise CommissionInvoiceValidationError(
                "Invoice must contain at least one line."
            )

        if any(
            not isinstance(
                line,
                CommissionInvoiceLine,
            )
            for line in lines
        ):
            raise CommissionInvoiceValidationError(
                "Invoice lines contain invalid values."
            )

        line_ids = [
            line.line_id
            for line in lines
        ]

        if len(line_ids) != len(set(line_ids)):
            raise CommissionInvoiceValidationError(
                "Duplicate invoice line_id is not allowed."
            )

        sequences = [
            line.sequence
            for line in lines
        ]

        if len(sequences) != len(set(sequences)):
            raise CommissionInvoiceValidationError(
                "Duplicate invoice line sequence is not allowed."
            )

        object.__setattr__(
            self,
            "lines",
            lines,
        )

        for field in (
            "subtotal",
            "adjustment_total",
            "total_due",
        ):
            value = getattr(self, field)

            if not isinstance(
                value,
                MonetaryAmount,
            ):
                raise CommissionInvoiceValidationError(
                    f"{field} must be MonetaryAmount."
                )

        currency_keys = {
            self.subtotal.currency.identity_key,
            self.adjustment_total.currency.identity_key,
            self.total_due.currency.identity_key,
        }

        if len(currency_keys) != 1:
            raise FinancialCurrencyMismatchError(
                "Invoice totals must use identical currency semantics."
            )

        line_currency_keys = {
            line.amount.currency.identity_key
            for line in lines
        }

        if (
            len(line_currency_keys) != 1
            or next(iter(line_currency_keys))
            != self.subtotal.currency.identity_key
        ):
            raise FinancialCurrencyMismatchError(
                "Invoice lines and totals must use identical currency."
            )

        line_sum = sum(
            (
                line.amount.amount
                for line in lines
            ),
            Decimal("0"),
        )

        if line_sum != self.subtotal.amount:
            raise CommissionInvoiceValidationError(
                "Invoice subtotal does not equal "
                "invoice line sum."
            )

        expected_total = (
            self.subtotal.amount
            + self.adjustment_total.amount
        )

        if expected_total != self.total_due.amount:
            raise CommissionInvoiceValidationError(
                "Invoice total_due does not equal "
                "subtotal plus adjustment_total."
            )

        object.__setattr__(
            self,
            "currency_code",
            self.currency_code.upper(),
        )

        if (
            self.currency_code
            != self.total_due.currency.code
        ):
            raise CommissionInvoiceValidationError(
                "currency_code does not match invoice currency."
            )

        issued_at = _aware(
            self.issued_at,
            "issued_at",
        )

        due_at = _aware(
            self.due_at,
            "due_at",
        )

        if due_at < issued_at:
            raise CommissionInvoiceValidationError(
                "due_at cannot be earlier than issued_at."
            )

        object.__setattr__(
            self,
            "issued_at",
            issued_at,
        )

        object.__setattr__(
            self,
            "due_at",
            due_at,
        )

        try:
            state = CommissionInvoiceState(
                self.state
            )
        except ValueError as exc:
            raise CommissionInvoiceValidationError(
                "Unsupported invoice state."
            ) from exc

        object.__setattr__(
            self,
            "state",
            state,
        )

        if self.external_invoice_reference is not None:
            object.__setattr__(
                self,
                "external_invoice_reference",
                _text(
                    self.external_invoice_reference,
                    "external_invoice_reference",
                ),
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
            raise CommissionInvoiceValidationError(
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

    @classmethod
    def create_from_allocation(
        cls,
        allocation: CommissionAllocation,
        *,
        invoice_number: str,
        issuer_reference: str,
        payer_reference: str,
        payee_reference: str,
        issued_at: datetime,
        due_at: datetime,
        authorization_reference: str,
        provenance_reference: str,
        invoice_id: str | None = None,
        external_invoice_reference: str | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> "CommissionInvoice":
        if not isinstance(
            allocation,
            CommissionAllocation,
        ):
            raise CommissionInvoiceValidationError(
                "allocation must be CommissionAllocation."
            )

        lines = tuple(
            CommissionInvoiceLine(
                line_id=(
                    f"{allocation.allocation_set_id}:{index}"
                ),
                line_type=(
                    CommissionInvoiceLineType.COMMISSION
                ),
                description=(
                    f"Commission allocation "
                    f"{line.entitlement_id}"
                ),
                reference_id=line.entitlement_id,
                amount=line.amount,
                sequence=index,
            )
            for index, line
            in enumerate(
                allocation.lines,
                start=1,
            )
        )

        return cls(
            invoice_id=(
                invoice_id
                or str(uuid4())
            ),
            tenant_id=allocation.tenant_id,
            commission_id=allocation.commission_id,
            allocation_set_id=(
                allocation.allocation_set_id
            ),
            settlement_id=(
                metadata.get("settlement_id", "")
                if metadata
                and metadata.get("settlement_id")
                else "UNBOUND"
            ),
            invoice_version=1,
            invoice_number=invoice_number,
            issuer_reference=issuer_reference,
            payer_reference=payer_reference,
            payee_reference=payee_reference,
            currency_code=(
                allocation.total_amount.currency.code
            ),
            lines=lines,
            subtotal=allocation.total_amount,
            adjustment_total=MonetaryAmount.zero(
                allocation.total_amount.currency
            ),
            total_due=allocation.total_amount,
            issued_at=issued_at,
            due_at=due_at,
            state=CommissionInvoiceState.DRAFT,
            authorization_reference=(
                authorization_reference
            ),
            provenance_reference=(
                provenance_reference
            ),
            external_invoice_reference=(
                external_invoice_reference
            ),
            metadata=(
                {}
                if metadata is None
                else metadata
            ),
        )

    @classmethod
    def create_from_settlement(
        cls,
        settlement: CommissionSettlement,
        *,
        invoice_number: str,
        issuer_reference: str,
        payer_reference: str,
        payee_reference: str,
        issued_at: datetime,
        due_at: datetime,
        authorization_reference: str,
        provenance_reference: str,
        invoice_id: str | None = None,
        external_invoice_reference: str | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> "CommissionInvoice":
        if not isinstance(
            settlement,
            CommissionSettlement,
        ):
            raise CommissionInvoiceValidationError(
                "settlement must be CommissionSettlement."
            )

        line = CommissionInvoiceLine(
            line_id=(
                f"{settlement.settlement_id}:1"
            ),
            line_type=(
                CommissionInvoiceLineType.COMMISSION
            ),
            description=(
                f"Commission settlement "
                f"{settlement.settlement_reference}"
            ),
            reference_id=settlement.settlement_id,
            amount=settlement.amount,
            sequence=1,
        )

        return cls(
            invoice_id=(
                invoice_id
                or str(uuid4())
            ),
            tenant_id=settlement.tenant_id,
            commission_id=settlement.commission_id,
            allocation_set_id=(
                settlement.allocation_set_id
            ),
            settlement_id=(
                settlement.settlement_id
            ),
            invoice_version=1,
            invoice_number=invoice_number,
            issuer_reference=issuer_reference,
            payer_reference=payer_reference,
            payee_reference=payee_reference,
            currency_code=(
                settlement.amount.currency.code
            ),
            lines=(line,),
            subtotal=settlement.amount,
            adjustment_total=MonetaryAmount.zero(
                settlement.amount.currency
            ),
            total_due=settlement.amount,
            issued_at=issued_at,
            due_at=due_at,
            state=CommissionInvoiceState.DRAFT,
            authorization_reference=(
                authorization_reference
            ),
            provenance_reference=(
                provenance_reference
            ),
            external_invoice_reference=(
                external_invoice_reference
            ),
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
            self.invoice_id,
            self.invoice_version,
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
                "Commission invoice crossed tenant scope."
            )

    def issue(self) -> "CommissionInvoice":
        if self.state is not CommissionInvoiceState.DRAFT:
            raise CommissionInvoiceValidationError(
                "Only DRAFT invoice can be issued."
            )

        return CommissionInvoice(
            **{
                **self.to_dict(
                    include_fingerprint=False
                ),
            }
        )

    def with_state(
        self,
        state: CommissionInvoiceState,
    ) -> "CommissionInvoice":
        return CommissionInvoice(
            invoice_id=self.invoice_id,
            tenant_id=self.tenant_id,
            commission_id=self.commission_id,
            allocation_set_id=self.allocation_set_id,
            settlement_id=self.settlement_id,
            invoice_version=self.invoice_version + 1,
            invoice_number=self.invoice_number,
            issuer_reference=self.issuer_reference,
            payer_reference=self.payer_reference,
            payee_reference=self.payee_reference,
            currency_code=self.currency_code,
            lines=self.lines,
            subtotal=self.subtotal,
            adjustment_total=self.adjustment_total,
            total_due=self.total_due,
            issued_at=self.issued_at,
            due_at=self.due_at,
            state=state,
            authorization_reference=(
                self.authorization_reference
            ),
            provenance_reference=(
                self.provenance_reference
            ),
            external_invoice_reference=(
                self.external_invoice_reference
            ),
            metadata=self.metadata,
        )

    def with_adjustment(
        self,
        adjustment: CommissionAdjustment,
    ) -> "CommissionInvoice":
        if not isinstance(
            adjustment,
            CommissionAdjustment,
        ):
            raise CommissionInvoiceValidationError(
                "adjustment must be CommissionAdjustment."
            )

        if (
            adjustment.tenant_id
            != self.tenant_id
            or adjustment.commission_id
            != self.commission_id
            or adjustment.settlement_id
            != self.settlement_id
        ):
            raise CommissionInvoiceValidationError(
                "Adjustment does not belong to invoice."
            )

        if adjustment.amount.currency.identity_key != (
            self.total_due.currency.identity_key
        ):
            raise FinancialCurrencyMismatchError(
                "Adjustment currency must match invoice."
            )

        sign = (
            Decimal("1")
            if adjustment.adjustment_type.value == "DEBIT"
            else Decimal("-1")
        )

        if adjustment.adjustment_type.value == "REVERSAL":
            sign = Decimal("-1")

        new_adjustment_total = (
            self.adjustment_total.amount
            + sign * adjustment.amount.amount
        )

        new_total = (
            self.subtotal.amount
            + new_adjustment_total
        )

        return CommissionInvoice(
            invoice_id=self.invoice_id,
            tenant_id=self.tenant_id,
            commission_id=self.commission_id,
            allocation_set_id=self.allocation_set_id,
            settlement_id=self.settlement_id,
            invoice_version=self.invoice_version + 1,
            invoice_number=self.invoice_number,
            issuer_reference=self.issuer_reference,
            payer_reference=self.payer_reference,
            payee_reference=self.payee_reference,
            currency_code=self.currency_code,
            lines=self.lines,
            subtotal=self.subtotal,
            adjustment_total=MonetaryAmount.create(
                new_adjustment_total,
                self.total_due.currency,
            ),
            total_due=MonetaryAmount.create(
                new_total,
                self.total_due.currency,
            ),
            issued_at=self.issued_at,
            due_at=self.due_at,
            state=self.state,
            authorization_reference=(
                self.authorization_reference
            ),
            provenance_reference=(
                self.provenance_reference
            ),
            external_invoice_reference=(
                self.external_invoice_reference
            ),
            metadata=self.metadata,
        )

    def to_dict(
        self,
        *,
        include_fingerprint: bool = True,
    ) -> dict[str, Any]:
        result = {
            "source_of_truth": (
                "CORE-008.COMMISSION_INVOICE"
            ),
            "schema_version": (
                CORE008_COMMISSION_INVOICE_SCHEMA_VERSION
            ),
            "invoice_id": self.invoice_id,
            "tenant_id": self.tenant_id,
            "commission_id": self.commission_id,
            "allocation_set_id": (
                self.allocation_set_id
            ),
            "settlement_id": self.settlement_id,
            "invoice_version": (
                self.invoice_version
            ),
            "invoice_number": (
                self.invoice_number
            ),
            "issuer_reference": (
                self.issuer_reference
            ),
            "payer_reference": (
                self.payer_reference
            ),
            "payee_reference": (
                self.payee_reference
            ),
            "currency_code": (
                self.currency_code
            ),
            "lines": [
                line.to_dict()
                for line in self.lines
            ],
            "subtotal": self.subtotal.to_dict(),
            "adjustment_total": (
                self.adjustment_total.to_dict()
            ),
            "total_due": (
                self.total_due.to_dict()
            ),
            "issued_at": (
                self.issued_at.isoformat()
            ),
            "due_at": (
                self.due_at.isoformat()
            ),
            "state": self.state.value,
            "authorization_reference": (
                self.authorization_reference
            ),
            "provenance_reference": (
                self.provenance_reference
            ),
            "external_invoice_reference": (
                self.external_invoice_reference
            ),
            "metadata": dict(self.metadata),
        }

        if include_fingerprint:
            result["immutable_fingerprint"] = (
                self.immutable_fingerprint
            )

        return result


__all__ = [
    "CORE008_COMMISSION_INVOICE_SCHEMA_VERSION",
    "CommissionInvoiceError",
    "CommissionInvoiceValidationError",
    "CommissionInvoiceState",
    "CommissionInvoiceLineType",
    "CommissionInvoiceLine",
    "CommissionInvoice",
]
