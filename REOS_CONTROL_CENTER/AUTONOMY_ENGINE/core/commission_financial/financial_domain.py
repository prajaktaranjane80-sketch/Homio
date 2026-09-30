"""CORE-008 Point 01 — Financial Domain.

This module owns only the foundational financial-domain vocabulary:
financial identity, financial subject references, currency semantics,
monetary amounts, rounding/precision rules, financial state, tenant scope,
and immutable financial-domain records.

Boundaries
----------
- REOS Control Center remains the project-state authority.
- CORE-001 remains identity / tenant / authorization authority.
- CORE-002 remains event infrastructure authority.
- CORE-003 remains lead/customer ownership authority.
- CORE-006 remains deal / transaction authority.
- CORE-007 remains trust / fraud / governance authority.
- ACRL remains reconstruction / continuity / checkpoint authority.

CORE-008 does not create a second identity engine, ownership engine,
event bus, audit engine, payment engine, Control Center, or ACRL engine.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import (
    Decimal,
    InvalidOperation,
    ROUND_CEILING,
    ROUND_DOWN,
    ROUND_FLOOR,
    ROUND_HALF_DOWN,
    ROUND_HALF_EVEN,
    ROUND_HALF_UP,
    ROUND_UP,
)
from enum import Enum
import re
from types import MappingProxyType
from typing import Any, Mapping
from uuid import uuid4


CORE008_FINANCIAL_DOMAIN_SCHEMA_VERSION = 1
CORE008_FINANCIAL_DOMAIN_SOURCE = "CORE-008.FINANCIAL_DOMAIN"


class FinancialDomainError(ValueError):
    """Base CORE-008 financial-domain error."""


class FinancialValidationError(FinancialDomainError):
    """Invalid financial-domain value."""


class FinancialTenantScopeError(FinancialDomainError):
    """Financial material crossed tenant scope."""


class FinancialCurrencyMismatchError(FinancialDomainError):
    """Arithmetic was attempted across different currencies."""


class FinancialPrecisionError(FinancialDomainError):
    """A monetary amount violated declared precision semantics."""


class RoundingMode(str, Enum):
    """Explicit Decimal rounding modes allowed by the financial domain."""

    CEILING = ROUND_CEILING
    DOWN = ROUND_DOWN
    FLOOR = ROUND_FLOOR
    HALF_DOWN = ROUND_HALF_DOWN
    HALF_EVEN = ROUND_HALF_EVEN
    HALF_UP = ROUND_HALF_UP
    UP = ROUND_UP


class FinancialState(str, Enum):
    """Foundational financial lifecycle vocabulary.

    Transition rules belong to the later bounded domains. This enum
    intentionally does not implement a second lifecycle engine.
    """

    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    ON_HOLD = "ON_HOLD"
    PENDING_SETTLEMENT = "PENDING_SETTLEMENT"
    SETTLED = "SETTLED"
    DISPUTED = "DISPUTED"
    REVERSED = "REVERSED"
    VOID = "VOID"


class FinancialSubjectType(str, Enum):
    """Typed references for later CORE-008 financial subjects."""

    COMMISSION = "COMMISSION"
    ENTITLEMENT = "ENTITLEMENT"
    CALCULATION = "CALCULATION"
    LEDGER_ENTRY = "LEDGER_ENTRY"
    SETTLEMENT = "SETTLEMENT"
    RECONCILIATION = "RECONCILIATION"
    ADJUSTMENT = "ADJUSTMENT"


_ROUNDING_MAP = {
    RoundingMode.CEILING: ROUND_CEILING,
    RoundingMode.DOWN: ROUND_DOWN,
    RoundingMode.FLOOR: ROUND_FLOOR,
    RoundingMode.HALF_DOWN: ROUND_HALF_DOWN,
    RoundingMode.HALF_EVEN: ROUND_HALF_EVEN,
    RoundingMode.HALF_UP: ROUND_HALF_UP,
    RoundingMode.UP: ROUND_UP,
}

_CURRENCY_RE = re.compile(r"^[A-Z]{3}$")


def _require_text(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise FinancialValidationError(
            f"{field_name} must be non-empty text."
        )
    return value.strip()


def _require_positive_int(value: int, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise FinancialValidationError(
            f"{field_name} must be a positive integer."
        )
    return value


def _require_nonnegative_int(value: int, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise FinancialValidationError(
            f"{field_name} must be an integer >= 0."
        )
    return value


def _to_decimal(
    value: Decimal | int | str,
    field_name: str,
) -> Decimal:
    if isinstance(value, bool):
        raise FinancialValidationError(
            f"{field_name} cannot be boolean."
        )

    if isinstance(value, float):
        raise FinancialValidationError(
            f"{field_name} must not accept binary floating-point values; "
            "use Decimal or a decimal string."
        )

    try:
        decimal_value = (
            value
            if isinstance(value, Decimal)
            else Decimal(str(value))
        )
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise FinancialValidationError(
            f"{field_name} must be a valid decimal value."
        ) from exc

    if not decimal_value.is_finite():
        raise FinancialValidationError(
            f"{field_name} must be finite."
        )

    return decimal_value


def _quantum(minor_unit: int) -> Decimal:
    return Decimal(1).scaleb(-minor_unit)


@dataclass(frozen=True, slots=True)
class Currency:
    """Immutable currency specification."""

    code: str
    minor_unit: int
    rounding_mode: RoundingMode = RoundingMode.HALF_EVEN

    def __post_init__(self) -> None:
        code = _require_text(self.code, "code").upper()

        if not _CURRENCY_RE.fullmatch(code):
            raise FinancialValidationError(
                "currency code must be exactly three uppercase letters."
            )

        minor_unit = _require_nonnegative_int(
            self.minor_unit,
            "minor_unit",
        )

        if minor_unit > 6:
            raise FinancialValidationError(
                "minor_unit must be <= 6 for CORE-008 foundation."
            )

        try:
            rounding_mode = RoundingMode(self.rounding_mode)
        except ValueError as exc:
            raise FinancialValidationError(
                "Unsupported financial rounding mode."
            ) from exc

        object.__setattr__(self, "code", code)
        object.__setattr__(self, "minor_unit", minor_unit)
        object.__setattr__(
            self,
            "rounding_mode",
            rounding_mode,
        )

    @property
    def quantum(self) -> Decimal:
        return _quantum(self.minor_unit)

    @property
    def identity_key(self) -> str:
        return (
            f"{self.code}:"
            f"{self.minor_unit}:"
            f"{self.rounding_mode.value}"
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "minor_unit": self.minor_unit,
            "rounding_mode": self.rounding_mode.value,
        }


@dataclass(frozen=True, slots=True)
class MonetaryAmount:
    """Immutable, currency-bound monetary amount."""

    amount: Decimal
    currency: Currency

    def __post_init__(self) -> None:
        if not isinstance(self.currency, Currency):
            raise FinancialValidationError(
                "currency must be a Currency."
            )

        value = _to_decimal(
            self.amount,
            "amount",
        )

        try:
            quantized = value.quantize(
                self.currency.quantum,
                rounding=_ROUNDING_MAP[
                    self.currency.rounding_mode
                ],
            )
        except InvalidOperation as exc:
            raise FinancialPrecisionError(
                "Amount exceeds supported decimal precision."
            ) from exc

        object.__setattr__(
            self,
            "amount",
            quantized,
        )

    @classmethod
    def create(
        cls,
        amount: Decimal | int | str,
        currency: Currency,
    ) -> "MonetaryAmount":
        return cls(
            amount=_to_decimal(
                amount,
                "amount",
            ),
            currency=currency,
        )

    @classmethod
    def zero(
        cls,
        currency: Currency,
    ) -> "MonetaryAmount":
        return cls(
            Decimal("0"),
            currency,
        )

    @property
    def is_zero(self) -> bool:
        return self.amount == 0

    @property
    def is_negative(self) -> bool:
        return self.amount < 0

    @property
    def as_minor_units(self) -> int:
        scale = 10 ** self.currency.minor_unit
        return int(self.amount * scale)

    def rounded(
        self,
        rounding_mode: RoundingMode,
    ) -> "MonetaryAmount":
        return MonetaryAmount(
            self.amount,
            Currency(
                code=self.currency.code,
                minor_unit=self.currency.minor_unit,
                rounding_mode=rounding_mode,
            ),
        )

    def add(
        self,
        other: "MonetaryAmount",
    ) -> "MonetaryAmount":
        self._assert_same_currency(other)

        return MonetaryAmount(
            self.amount + other.amount,
            self.currency,
        )

    def subtract(
        self,
        other: "MonetaryAmount",
    ) -> "MonetaryAmount":
        self._assert_same_currency(other)

        return MonetaryAmount(
            self.amount - other.amount,
            self.currency,
        )

    def _assert_same_currency(
        self,
        other: "MonetaryAmount",
    ) -> None:
        if not isinstance(
            other,
            MonetaryAmount,
        ):
            raise FinancialValidationError(
                "Arithmetic operand must be MonetaryAmount."
            )

        if (
            self.currency.identity_key
            != other.currency.identity_key
        ):
            raise FinancialCurrencyMismatchError(
                "Monetary amounts use different currency semantics."
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "amount": format(
                self.amount,
                "f",
            ),
            "currency": self.currency.to_dict(),
        }


@dataclass(frozen=True, slots=True)
class FinancialSubject:
    """Immutable typed reference to a financial subject."""

    subject_type: FinancialSubjectType
    subject_id: str
    subject_version: int = 1

    def __post_init__(self) -> None:
        try:
            subject_type = FinancialSubjectType(
                self.subject_type
            )
        except ValueError as exc:
            raise FinancialValidationError(
                "Unsupported financial subject type."
            ) from exc

        object.__setattr__(
            self,
            "subject_type",
            subject_type,
        )

        object.__setattr__(
            self,
            "subject_id",
            _require_text(
                self.subject_id,
                "subject_id",
            ),
        )

        object.__setattr__(
            self,
            "subject_version",
            _require_positive_int(
                self.subject_version,
                "subject_version",
            ),
        )

    @property
    def identity_key(self) -> tuple[str, str]:
        return (
            self.subject_type.value,
            self.subject_id,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "subject_type": self.subject_type.value,
            "subject_id": self.subject_id,
            "subject_version": self.subject_version,
        }


@dataclass(frozen=True, slots=True)
class FinancialIdentity:
    """Immutable tenant-scoped financial identity."""

    financial_id: str
    tenant_id: str
    subject: FinancialSubject
    identity_version: int = 1

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "financial_id",
            _require_text(
                self.financial_id,
                "financial_id",
            ),
        )

        object.__setattr__(
            self,
            "tenant_id",
            _require_text(
                self.tenant_id,
                "tenant_id",
            ),
        )

        if not isinstance(
            self.subject,
            FinancialSubject,
        ):
            raise FinancialValidationError(
                "subject must be FinancialSubject."
            )

        object.__setattr__(
            self,
            "identity_version",
            _require_positive_int(
                self.identity_version,
                "identity_version",
            ),
        )

    @property
    def identity_key(self) -> tuple[str, str, str, str]:
        return (
            self.tenant_id,
            self.subject.subject_type.value,
            self.subject.subject_id,
            self.financial_id,
        )

    @property
    def immutable_fingerprint(self) -> str:
        from hashlib import sha256
        import json

        payload = {
            "financial_id": self.financial_id,
            "tenant_id": self.tenant_id,
            "subject": self.subject.to_dict(),
            "identity_version": self.identity_version,
            "schema_version": (
                CORE008_FINANCIAL_DOMAIN_SCHEMA_VERSION
            ),
        }

        raw = json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")

        return sha256(raw).hexdigest()

    def assert_tenant(
        self,
        tenant_id: str,
    ) -> None:
        tenant_id = _require_text(
            tenant_id,
            "tenant_id",
        )

        if tenant_id != self.tenant_id:
            raise FinancialTenantScopeError(
                "Financial identity crosses tenant scope."
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "financial_id": self.financial_id,
            "tenant_id": self.tenant_id,
            "subject": self.subject.to_dict(),
            "identity_version": self.identity_version,
            "schema_version": (
                CORE008_FINANCIAL_DOMAIN_SCHEMA_VERSION
            ),
            "immutable_fingerprint": (
                self.immutable_fingerprint
            ),
        }


@dataclass(frozen=True, slots=True)
class FinancialDomainRecord:
    """Immutable foundational financial-domain snapshot.

    Later CORE-008 points attach commission terms, calculations,
    entitlements, ledger references, settlement and reconciliation through
    their own bounded contracts. This record intentionally does not
    implement their lifecycle or concurrency engines.
    """

    identity: FinancialIdentity
    state: FinancialState = FinancialState.DRAFT
    amount: MonetaryAmount | None = None
    metadata: Mapping[str, Any] = ()

    def __post_init__(self) -> None:
        if not isinstance(
            self.identity,
            FinancialIdentity,
        ):
            raise FinancialValidationError(
                "identity must be FinancialIdentity."
            )

        try:
            state = FinancialState(self.state)
        except ValueError as exc:
            raise FinancialValidationError(
                "Unsupported financial state."
            ) from exc

        object.__setattr__(
            self,
            "state",
            state,
        )

        if self.amount is not None and not isinstance(
            self.amount,
            MonetaryAmount,
        ):
            raise FinancialValidationError(
                "amount must be MonetaryAmount or None."
            )

        metadata = self.metadata

        if metadata == ():
            metadata = {}

        if not isinstance(
            metadata,
            Mapping,
        ):
            raise FinancialValidationError(
                "metadata must be a mapping."
            )

        normalized: dict[
            str,
            str | int | bool | None,
        ] = {}

        for key, value in metadata.items():
            if (
                not isinstance(key, str)
                or not key.strip()
            ):
                raise FinancialValidationError(
                    "metadata keys must be non-empty strings."
                )

            if (
                not isinstance(
                    value,
                    (str, int, bool),
                )
                and value is not None
            ):
                raise FinancialValidationError(
                    "metadata values must be scalar "
                    "JSON-safe primitives."
                )

            normalized[key.strip()] = value

        object.__setattr__(
            self,
            "metadata",
            MappingProxyType(normalized),
        )

    @property
    def tenant_id(self) -> str:
        return self.identity.tenant_id

    @property
    def financial_id(self) -> str:
        return self.identity.financial_id

    @property
    def identity_key(
        self,
    ) -> tuple[str, str, str, str]:
        return self.identity.identity_key

    @property
    def immutable_fingerprint(self) -> str:
        from hashlib import sha256
        import json

        payload = self.to_dict(
            include_fingerprint=False,
        )

        raw = json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")

        return sha256(raw).hexdigest()

    def assert_tenant(
        self,
        tenant_id: str,
    ) -> None:
        self.identity.assert_tenant(
            tenant_id
        )

    def to_dict(
        self,
        *,
        include_fingerprint: bool = True,
    ) -> dict[str, Any]:
        result: dict[str, Any] = {
            "source_of_truth": (
                CORE008_FINANCIAL_DOMAIN_SOURCE
            ),
            "schema_version": (
                CORE008_FINANCIAL_DOMAIN_SCHEMA_VERSION
            ),
            "identity": self.identity.to_dict(),
            "state": self.state.value,
            "amount": (
                self.amount.to_dict()
                if self.amount is not None
                else None
            ),
            "metadata": dict(self.metadata),
        }

        if include_fingerprint:
            result["immutable_fingerprint"] = (
                self.immutable_fingerprint
            )

        return result


def new_financial_identity(
    *,
    tenant_id: str,
    subject_type: FinancialSubjectType,
    subject_id: str,
) -> FinancialIdentity:
    """Create a new tenant-scoped financial identity."""

    return FinancialIdentity(
        financial_id=str(uuid4()),
        tenant_id=tenant_id,
        subject=FinancialSubject(
            subject_type=subject_type,
            subject_id=subject_id,
        ),
    )


__all__ = [
    "CORE008_FINANCIAL_DOMAIN_SCHEMA_VERSION",
    "CORE008_FINANCIAL_DOMAIN_SOURCE",
    "FinancialDomainError",
    "FinancialValidationError",
    "FinancialTenantScopeError",
    "FinancialCurrencyMismatchError",
    "FinancialPrecisionError",
    "RoundingMode",
    "FinancialState",
    "FinancialSubjectType",
    "Currency",
    "MonetaryAmount",
    "FinancialSubject",
    "FinancialIdentity",
    "FinancialDomainRecord",
    "new_financial_identity",
]