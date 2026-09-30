from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Any, Mapping

from ..contract_primitives import deep_freeze, fingerprint
from .commission_settlement import CommissionSettlement
from .financial_domain import (
    FinancialCurrencyMismatchError,
    FinancialTenantScopeError,
    MonetaryAmount,
)


CORE008_COMMISSION_RECONCILIATION_SCHEMA_VERSION = 1


class CommissionReconciliationError(ValueError):
    """Base reconciliation error."""


class CommissionReconciliationValidationError(
    CommissionReconciliationError
):
    """Invalid reconciliation input."""


class CommissionReconciliationState(str, Enum):
    OPEN = "OPEN"
    MATCHED = "MATCHED"
    PARTIALLY_MATCHED = "PARTIALLY_MATCHED"
    VARIANCE = "VARIANCE"
    EXCEPTION = "EXCEPTION"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"


class CommissionReconciliationMatchType(str, Enum):
    EXACT = "EXACT"
    PARTIAL = "PARTIAL"
    OVERPAYMENT = "OVERPAYMENT"
    UNDERPAYMENT = "UNDERPAYMENT"
    REFERENCE_ONLY = "REFERENCE_ONLY"


def _text(value: str, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise CommissionReconciliationValidationError(
            f"{field} must be non-empty text."
        )
    return value.strip()


def _aware(value: datetime, field: str) -> datetime:
    if (
        not isinstance(value, datetime)
        or value.tzinfo is None
        or value.utcoffset() is None
    ):
        raise CommissionReconciliationValidationError(
            f"{field} must be timezone-aware."
        )
    return value.astimezone(timezone.utc)


def _positive(value: int, field: str) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or value < 1
    ):
        raise CommissionReconciliationValidationError(
            f"{field} must be a positive integer."
        )
    return value


@dataclass(frozen=True, slots=True)
class CommissionExternalSettlementEvidence:
    """Immutable external settlement observation.

    This is evidence received from an external payment/banking system.
    It does not become the payment system of record.
    """

    evidence_id: str
    tenant_id: str
    external_reference: str
    provider_reference: str
    observed_amount: MonetaryAmount
    observed_at: datetime
    status_code: str
    source_version: int
    metadata: Mapping[str, Any] = ()

    def __post_init__(self) -> None:
        for field in (
            "evidence_id",
            "tenant_id",
            "external_reference",
            "provider_reference",
            "status_code",
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
            "source_version",
            _positive(
                self.source_version,
                "source_version",
            ),
        )

        if not isinstance(
            self.observed_amount,
            MonetaryAmount,
        ):
            raise CommissionReconciliationValidationError(
                "observed_amount must be MonetaryAmount."
            )

        if self.observed_amount.amount < 0:
            raise CommissionReconciliationValidationError(
                "observed_amount cannot be negative."
            )

        object.__setattr__(
            self,
            "observed_at",
            _aware(
                self.observed_at,
                "observed_at",
            ),
        )

        metadata = (
            {}
            if self.metadata == ()
            else self.metadata
        )

        if not isinstance(metadata, Mapping):
            raise CommissionReconciliationValidationError(
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

    @property
    def immutable_fingerprint(self) -> str:
        return fingerprint(
            self.to_dict(
                include_fingerprint=False
            )
        )

    def to_dict(
        self,
        *,
        include_fingerprint: bool = True,
    ) -> dict[str, Any]:
        result = {
            "evidence_id": self.evidence_id,
            "tenant_id": self.tenant_id,
            "external_reference": (
                self.external_reference
            ),
            "provider_reference": (
                self.provider_reference
            ),
            "observed_amount": (
                self.observed_amount.to_dict()
            ),
            "observed_at": (
                self.observed_at.isoformat()
            ),
            "status_code": self.status_code,
            "source_version": self.source_version,
            "metadata": dict(self.metadata),
        }

        if include_fingerprint:
            result["immutable_fingerprint"] = (
                self.immutable_fingerprint
            )

        return result


@dataclass(frozen=True, slots=True)
class CommissionReconciliation:
    """Immutable reconciliation result.

    CORE-008 reconciles expected settlement against observed evidence.
    It does not execute, reverse, or post payment transactions.
    """

    reconciliation_id: str
    tenant_id: str
    commission_id: str
    settlement_id: str
    reconciliation_version: int
    expected_amount: MonetaryAmount
    observed_amount: MonetaryAmount
    variance_amount: MonetaryAmount
    match_type: CommissionReconciliationMatchType
    state: CommissionReconciliationState
    external_evidence_id: str
    settlement_reference: str
    reconciled_at: datetime
    reconciliation_reference: str
    provenance_reference: str
    variance_tolerance: MonetaryAmount
    metadata: Mapping[str, Any] = ()

    def __post_init__(self) -> None:
        for field in (
            "reconciliation_id",
            "tenant_id",
            "commission_id",
            "settlement_id",
            "external_evidence_id",
            "settlement_reference",
            "reconciliation_reference",
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
            "reconciliation_version",
            _positive(
                self.reconciliation_version,
                "reconciliation_version",
            ),
        )

        for field in (
            "expected_amount",
            "observed_amount",
            "variance_amount",
            "variance_tolerance",
        ):
            value = getattr(self, field)

            if not isinstance(
                value,
                MonetaryAmount,
            ):
                raise CommissionReconciliationValidationError(
                    f"{field} must be MonetaryAmount."
                )

        currencies = {
            self.expected_amount.currency.identity_key,
            self.observed_amount.currency.identity_key,
            self.variance_amount.currency.identity_key,
            self.variance_tolerance.currency.identity_key,
        }

        if len(currencies) != 1:
            raise FinancialCurrencyMismatchError(
                "All reconciliation monetary values must "
                "use identical currency semantics."
            )

        if (
            self.variance_tolerance.amount < 0
        ):
            raise CommissionReconciliationValidationError(
                "variance_tolerance cannot be negative."
            )

        expected_variance = (
            self.observed_amount.amount
            - self.expected_amount.amount
        )

        if self.variance_amount.amount != expected_variance:
            raise CommissionReconciliationValidationError(
                "variance_amount does not match "
                "observed minus expected."
            )

        try:
            match_type = CommissionReconciliationMatchType(
                self.match_type
            )
            state = CommissionReconciliationState(
                self.state
            )
        except ValueError as exc:
            raise CommissionReconciliationValidationError(
                "Unsupported reconciliation enum."
            ) from exc

        object.__setattr__(
            self,
            "match_type",
            match_type,
        )
        object.__setattr__(
            self,
            "state",
            state,
        )

        object.__setattr__(
            self,
            "reconciled_at",
            _aware(
                self.reconciled_at,
                "reconciled_at",
            ),
        )

        metadata = (
            {}
            if self.metadata == ()
            else self.metadata
        )

        if not isinstance(metadata, Mapping):
            raise CommissionReconciliationValidationError(
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
    def reconcile(
        cls,
        settlement: CommissionSettlement,
        evidence: CommissionExternalSettlementEvidence,
        *,
        reconciliation_id: str,
        reconciliation_version: int = 1,
        variance_tolerance: MonetaryAmount | None = None,
        reconciled_at: datetime,
        reconciliation_reference: str,
        provenance_reference: str,
        metadata: Mapping[str, Any] | None = None,
    ) -> "CommissionReconciliation":
        if not isinstance(
            settlement,
            CommissionSettlement,
        ):
            raise CommissionReconciliationValidationError(
                "settlement must be CommissionSettlement."
            )

        if not isinstance(
            evidence,
            CommissionExternalSettlementEvidence,
        ):
            raise CommissionReconciliationValidationError(
                "evidence must be "
                "CommissionExternalSettlementEvidence."
            )

        if settlement.tenant_id != evidence.tenant_id:
            raise CommissionReconciliationValidationError(
                "Settlement and evidence tenant mismatch."
            )

        if (
            settlement.amount.currency.identity_key
            != evidence.observed_amount.currency.identity_key
        ):
            raise FinancialCurrencyMismatchError(
                "Settlement and observed amount currency mismatch."
            )

        tolerance = (
            MonetaryAmount.zero(
                settlement.amount.currency
            )
            if variance_tolerance is None
            else variance_tolerance
        )

        if (
            tolerance.currency.identity_key
            != settlement.amount.currency.identity_key
        ):
            raise FinancialCurrencyMismatchError(
                "Variance tolerance currency mismatch."
            )

        expected = settlement.amount.amount
        observed = evidence.observed_amount.amount
        variance = observed - expected

        if abs(variance) <= tolerance.amount:
            match_type = (
                CommissionReconciliationMatchType.EXACT
            )
            state = CommissionReconciliationState.MATCHED

        elif variance < 0:
            match_type = (
                CommissionReconciliationMatchType.UNDERPAYMENT
            )
            state = (
                CommissionReconciliationState.VARIANCE
            )

        else:
            match_type = (
                CommissionReconciliationMatchType.OVERPAYMENT
            )
            state = (
                CommissionReconciliationState.VARIANCE
            )

        variance_amount = MonetaryAmount.create(
            variance,
            settlement.amount.currency,
        )

        return cls(
            reconciliation_id=reconciliation_id,
            tenant_id=settlement.tenant_id,
            commission_id=settlement.commission_id,
            settlement_id=settlement.settlement_id,
            reconciliation_version=reconciliation_version,
            expected_amount=settlement.amount,
            observed_amount=evidence.observed_amount,
            variance_amount=variance_amount,
            match_type=match_type,
            state=state,
            external_evidence_id=evidence.evidence_id,
            settlement_reference=(
                settlement.settlement_reference
            ),
            reconciled_at=reconciled_at,
            reconciliation_reference=(
                reconciliation_reference
            ),
            provenance_reference=(
                provenance_reference
            ),
            variance_tolerance=tolerance,
            metadata=(
                {}
                if metadata is None
                else metadata
            ),
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
                "Reconciliation crossed tenant scope."
            )

    def to_dict(
        self,
        *,
        include_fingerprint: bool = True,
    ) -> dict[str, Any]:
        result = {
            "source_of_truth": (
                "CORE-008.COMMISSION_RECONCILIATION"
            ),
            "schema_version": (
                CORE008_COMMISSION_RECONCILIATION_SCHEMA_VERSION
            ),
            "reconciliation_id": (
                self.reconciliation_id
            ),
            "tenant_id": self.tenant_id,
            "commission_id": self.commission_id,
            "settlement_id": self.settlement_id,
            "reconciliation_version": (
                self.reconciliation_version
            ),
            "expected_amount": (
                self.expected_amount.to_dict()
            ),
            "observed_amount": (
                self.observed_amount.to_dict()
            ),
            "variance_amount": (
                self.variance_amount.to_dict()
            ),
            "match_type": self.match_type.value,
            "state": self.state.value,
            "external_evidence_id": (
                self.external_evidence_id
            ),
            "settlement_reference": (
                self.settlement_reference
            ),
            "reconciled_at": (
                self.reconciled_at.isoformat()
            ),
            "reconciliation_reference": (
                self.reconciliation_reference
            ),
            "provenance_reference": (
                self.provenance_reference
            ),
            "variance_tolerance": (
                self.variance_tolerance.to_dict()
            ),
            "metadata": dict(self.metadata),
        }

        if include_fingerprint:
            result["immutable_fingerprint"] = (
                self.immutable_fingerprint
            )

        return result


__all__ = [
    "CORE008_COMMISSION_RECONCILIATION_SCHEMA_VERSION",
    "CommissionReconciliationError",
    "CommissionReconciliationValidationError",
    "CommissionReconciliationState",
    "CommissionReconciliationMatchType",
    "CommissionExternalSettlementEvidence",
    "CommissionReconciliation",
]
