from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Any, Mapping
from uuid import uuid4

from ..contract_primitives import deep_freeze, fingerprint
from .commission_invoice import CommissionInvoice
from .financial_domain import (
    FinancialCurrencyMismatchError,
    FinancialTenantScopeError,
    MonetaryAmount,
)


CORE008_COMMISSION_TAX_SCHEMA_VERSION = 1


class CommissionTaxError(ValueError):
    """Base tax-domain error."""


class CommissionTaxValidationError(
    CommissionTaxError
):
    """Invalid commission tax record."""


class CommissionTaxComponentType(str, Enum):
    TAX = "TAX"
    WITHHOLDING = "WITHHOLDING"


class CommissionTaxState(str, Enum):
    DRAFT = "DRAFT"
    ASSESSED = "ASSESSED"
    CONFIRMED = "CONFIRMED"
    VOID = "VOID"
    SUPERSEDED = "SUPERSEDED"


def _text(value: str, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise CommissionTaxValidationError(
            f"{field} must be non-empty text."
        )
    return value.strip()


def _aware(value: datetime, field: str) -> datetime:
    if (
        not isinstance(value, datetime)
        or value.tzinfo is None
        or value.utcoffset() is None
    ):
        raise CommissionTaxValidationError(
            f"{field} must be timezone-aware."
        )

    return value.astimezone(timezone.utc)


def _positive(value: int, field: str) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or value < 1
    ):
        raise CommissionTaxValidationError(
            f"{field} must be a positive integer."
        )
    return value


def _decimal(
    value: Decimal | int | str,
    field: str,
) -> Decimal:
    if isinstance(value, bool):
        raise CommissionTaxValidationError(
            f"{field} cannot be boolean."
        )

    try:
        result = (
            value
            if isinstance(value, Decimal)
            else Decimal(str(value))
        )
    except Exception as exc:
        raise CommissionTaxValidationError(
            f"{field} must be a valid decimal."
        ) from exc

    if not result.is_finite():
        raise CommissionTaxValidationError(
            f"{field} must be finite."
        )

    return result


@dataclass(frozen=True, slots=True)
class CommissionTaxRuleReference:
    """Immutable external tax-rule authority reference.

    CORE-008 stores the rule used for assessment.
    It does not become the authoritative tax-policy engine.
    """

    rule_reference: str
    jurisdiction_code: str
    rule_version: int
    effective_from: datetime
    effective_to: datetime | None = None
    source_reference: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "rule_reference",
            _text(
                self.rule_reference,
                "rule_reference",
            ),
        )

        object.__setattr__(
            self,
            "jurisdiction_code",
            _text(
                self.jurisdiction_code,
                "jurisdiction_code",
            ).upper(),
        )

        object.__setattr__(
            self,
            "rule_version",
            _positive(
                self.rule_version,
                "rule_version",
            ),
        )

        start = _aware(
            self.effective_from,
            "effective_from",
        )

        object.__setattr__(
            self,
            "effective_from",
            start,
        )

        if self.effective_to is not None:
            end = _aware(
                self.effective_to,
                "effective_to",
            )

            if end <= start:
                raise CommissionTaxValidationError(
                    "effective_to must be later "
                    "than effective_from."
                )

            object.__setattr__(
                self,
                "effective_to",
                end,
            )

        source_reference = self.source_reference

        if source_reference:
            object.__setattr__(
                self,
                "source_reference",
                source_reference.strip(),
            )

    def applies_at(self, at: datetime) -> bool:
        instant = _aware(
            at,
            "at",
        )

        if instant < self.effective_from:
            return False

        return (
            self.effective_to is None
            or instant < self.effective_to
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "rule_reference": self.rule_reference,
            "jurisdiction_code": (
                self.jurisdiction_code
            ),
            "rule_version": self.rule_version,
            "effective_from": (
                self.effective_from.isoformat()
            ),
            "effective_to": (
                self.effective_to.isoformat()
                if self.effective_to is not None
                else None
            ),
            "source_reference": (
                self.source_reference
            ),
        }


@dataclass(frozen=True, slots=True)
class CommissionTaxComponent:
    """One immutable tax or withholding component."""

    component_id: str
    component_type: CommissionTaxComponentType
    code: str
    description: str
    jurisdiction_code: str
    rate_percent: Decimal
    base_amount: MonetaryAmount
    amount: MonetaryAmount
    rule: CommissionTaxRuleReference
    recoverable: bool = False
    metadata: Mapping[str, Any] = ()

    def __post_init__(self) -> None:
        for field in (
            "component_id",
            "code",
            "description",
            "jurisdiction_code",
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
            component_type = CommissionTaxComponentType(
                self.component_type
            )
        except ValueError as exc:
            raise CommissionTaxValidationError(
                "Unsupported tax component type."
            ) from exc

        object.__setattr__(
            self,
            "component_type",
            component_type,
        )

        rate = _decimal(
            self.rate_percent,
            "rate_percent",
        )

        if rate < 0 or rate > 100:
            raise CommissionTaxValidationError(
                "rate_percent must be between 0 and 100."
            )

        object.__setattr__(
            self,
            "rate_percent",
            rate,
        )

        if not isinstance(
            self.base_amount,
            MonetaryAmount,
        ):
            raise CommissionTaxValidationError(
                "base_amount must be MonetaryAmount."
            )

        if not isinstance(
            self.amount,
            MonetaryAmount,
        ):
            raise CommissionTaxValidationError(
                "amount must be MonetaryAmount."
            )

        if (
            self.base_amount.currency.identity_key
            != self.amount.currency.identity_key
        ):
            raise FinancialCurrencyMismatchError(
                "Tax base and tax amount currency mismatch."
            )

        if self.amount.amount < 0:
            raise CommissionTaxValidationError(
                "Tax component amount cannot be negative."
            )

        if not isinstance(
            self.rule,
            CommissionTaxRuleReference,
        ):
            raise CommissionTaxValidationError(
                "rule must be CommissionTaxRuleReference."
            )

        if (
            self.jurisdiction_code.upper()
            != self.rule.jurisdiction_code
        ):
            raise CommissionTaxValidationError(
                "Component jurisdiction does not match rule."
            )

        if not isinstance(
            self.recoverable,
            bool,
        ):
            raise CommissionTaxValidationError(
                "recoverable must be boolean."
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
            raise CommissionTaxValidationError(
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
    def calculate(
        cls,
        *,
        component_id: str | None = None,
        component_type: CommissionTaxComponentType,
        code: str,
        description: str,
        jurisdiction_code: str,
        rate_percent: Decimal | int | str,
        base_amount: MonetaryAmount,
        rule: CommissionTaxRuleReference,
        recoverable: bool = False,
        metadata: Mapping[str, Any] | None = None,
    ) -> "CommissionTaxComponent":
        rate = _decimal(
            rate_percent,
            "rate_percent",
        )

        raw_amount = (
            base_amount.amount
            * rate
            / Decimal("100")
        )

        amount = MonetaryAmount.create(
            raw_amount,
            base_amount.currency,
        )

        return cls(
            component_id=(
                component_id
                or str(uuid4())
            ),
            component_type=component_type,
            code=code,
            description=description,
            jurisdiction_code=jurisdiction_code,
            rate_percent=rate,
            base_amount=base_amount,
            amount=amount,
            rule=rule,
            recoverable=recoverable,
            metadata=(
                {}
                if metadata is None
                else metadata
            ),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "component_id": self.component_id,
            "component_type": (
                self.component_type.value
            ),
            "code": self.code,
            "description": self.description,
            "jurisdiction_code": (
                self.jurisdiction_code
            ),
            "rate_percent": format(
                self.rate_percent,
                "f",
            ),
            "base_amount": (
                self.base_amount.to_dict()
            ),
            "amount": self.amount.to_dict(),
            "rule": self.rule.to_dict(),
            "recoverable": self.recoverable,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class CommissionTaxAssessment:
    """Immutable invoice-level tax and withholding assessment."""

    assessment_id: str
    tenant_id: str
    commission_id: str
    invoice_id: str
    assessment_version: int
    taxable_base: MonetaryAmount
    tax_components: tuple[
        CommissionTaxComponent,
        ...
    ]
    withholding_components: tuple[
        CommissionTaxComponent,
        ...
    ]
    total_tax: MonetaryAmount
    total_withholding: MonetaryAmount
    net_payable_effect: MonetaryAmount
    assessed_at: datetime
    provenance_reference: str
    authorization_reference: str
    state: CommissionTaxState = (
        CommissionTaxState.DRAFT
    )
    metadata: Mapping[str, Any] = ()

    def __post_init__(self) -> None:
        for field in (
            "assessment_id",
            "tenant_id",
            "commission_id",
            "invoice_id",
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
            "assessment_version",
            _positive(
                self.assessment_version,
                "assessment_version",
            ),
        )

        for field in (
            "taxable_base",
            "total_tax",
            "total_withholding",
            "net_payable_effect",
        ):
            if not isinstance(
                getattr(self, field),
                MonetaryAmount,
            ):
                raise CommissionTaxValidationError(
                    f"{field} must be MonetaryAmount."
                )

        currency_keys = {
            self.taxable_base.currency.identity_key,
            self.total_tax.currency.identity_key,
            self.total_withholding.currency.identity_key,
            self.net_payable_effect.currency.identity_key,
        }

        if len(currency_keys) != 1:
            raise FinancialCurrencyMismatchError(
                "Assessment monetary values must use "
                "identical currency semantics."
            )

        taxes = tuple(self.tax_components)
        withholdings = tuple(
            self.withholding_components
        )

        for component in (
            taxes + withholdings
        ):
            if not isinstance(
                component,
                CommissionTaxComponent,
            ):
                raise CommissionTaxValidationError(
                    "Assessment contains invalid tax component."
                )

            if (
                component.base_amount.currency.identity_key
                != self.taxable_base.currency.identity_key
            ):
                raise FinancialCurrencyMismatchError(
                    "Tax component currency differs "
                    "from assessment currency."
                )

        expected_tax = sum(
            (
                component.amount.amount
                for component in taxes
            ),
            Decimal("0"),
        )

        expected_withholding = sum(
            (
                component.amount.amount
                for component in withholdings
            ),
            Decimal("0"),
        )

        if (
            expected_tax
            != self.total_tax.amount
        ):
            raise CommissionTaxValidationError(
                "total_tax does not equal "
                "tax component sum."
            )

        if (
            expected_withholding
            != self.total_withholding.amount
        ):
            raise CommissionTaxValidationError(
                "total_withholding does not equal "
                "withholding component sum."
            )

        expected_net_effect = (
            self.total_tax.amount
            - self.total_withholding.amount
        )

        if (
            expected_net_effect
            != self.net_payable_effect.amount
        ):
            raise CommissionTaxValidationError(
                "net_payable_effect does not equal "
                "tax minus withholding."
            )

        object.__setattr__(
            self,
            "tax_components",
            taxes,
        )
        object.__setattr__(
            self,
            "withholding_components",
            withholdings,
        )

        object.__setattr__(
            self,
            "assessed_at",
            _aware(
                self.assessed_at,
                "assessed_at",
            ),
        )

        try:
            state = CommissionTaxState(
                self.state
            )
        except ValueError as exc:
            raise CommissionTaxValidationError(
                "Unsupported tax assessment state."
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
            raise CommissionTaxValidationError(
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
    def assess_invoice(
        cls,
        invoice: CommissionInvoice,
        *,
        taxable_base: MonetaryAmount,
        tax_components: tuple[
            CommissionTaxComponent,
            ...] = (),
        withholding_components: tuple[
            CommissionTaxComponent,
            ...] = (),
        assessment_id: str | None = None,
        assessment_version: int = 1,
        assessed_at: datetime,
        provenance_reference: str,
        authorization_reference: str,
        state: CommissionTaxState = (
            CommissionTaxState.ASSESSED
        ),
        metadata: Mapping[str, Any] | None = None,
    ) -> "CommissionTaxAssessment":
        if not isinstance(
            invoice,
            CommissionInvoice,
        ):
            raise CommissionTaxValidationError(
                "invoice must be CommissionInvoice."
            )

        if not isinstance(
            taxable_base,
            MonetaryAmount,
        ):
            raise CommissionTaxValidationError(
                "taxable_base must be MonetaryAmount."
            )

        if (
            taxable_base.currency.identity_key
            != invoice.total_due.currency.identity_key
        ):
            raise FinancialCurrencyMismatchError(
                "Taxable base currency must match invoice."
            )

        if taxable_base.amount < 0:
            raise CommissionTaxValidationError(
                "taxable_base cannot be negative."
            )

        taxes = tuple(tax_components)
        withholdings = tuple(
            withholding_components
        )

        total_tax = MonetaryAmount.create(
            sum(
                (
                    component.amount.amount
                    for component in taxes
                ),
                Decimal("0"),
            ),
            taxable_base.currency,
        )

        total_withholding = MonetaryAmount.create(
            sum(
                (
                    component.amount.amount
                    for component in withholdings
                ),
                Decimal("0"),
            ),
            taxable_base.currency,
        )

        net_effect = MonetaryAmount.create(
            total_tax.amount
            - total_withholding.amount,
            taxable_base.currency,
        )

        return cls(
            assessment_id=(
                assessment_id
                or str(uuid4())
            ),
            tenant_id=invoice.tenant_id,
            commission_id=invoice.commission_id,
            invoice_id=invoice.invoice_id,
            assessment_version=assessment_version,
            taxable_base=taxable_base,
            tax_components=taxes,
            withholding_components=withholdings,
            total_tax=total_tax,
            total_withholding=total_withholding,
            net_payable_effect=net_effect,
            assessed_at=assessed_at,
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
            self.assessment_id,
            self.assessment_version,
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
                "Tax assessment crossed tenant scope."
            )

    def to_dict(
        self,
        *,
        include_fingerprint: bool = True,
    ) -> dict[str, Any]:
        result = {
            "source_of_truth": (
                "CORE-008.COMMISSION_TAX"
            ),
            "schema_version": (
                CORE008_COMMISSION_TAX_SCHEMA_VERSION
            ),
            "assessment_id": (
                self.assessment_id
            ),
            "tenant_id": self.tenant_id,
            "commission_id": (
                self.commission_id
            ),
            "invoice_id": self.invoice_id,
            "assessment_version": (
                self.assessment_version
            ),
            "taxable_base": (
                self.taxable_base.to_dict()
            ),
            "tax_components": [
                component.to_dict()
                for component in self.tax_components
            ],
            "withholding_components": [
                component.to_dict()
                for component
                in self.withholding_components
            ],
            "total_tax": (
                self.total_tax.to_dict()
            ),
            "total_withholding": (
                self.total_withholding.to_dict()
            ),
            "net_payable_effect": (
                self.net_payable_effect.to_dict()
            ),
            "assessed_at": (
                self.assessed_at.isoformat()
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
    "CORE008_COMMISSION_TAX_SCHEMA_VERSION",
    "CommissionTaxError",
    "CommissionTaxValidationError",
    "CommissionTaxComponentType",
    "CommissionTaxState",
    "CommissionTaxRuleReference",
    "CommissionTaxComponent",
    "CommissionTaxAssessment",
]
