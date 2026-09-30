from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Mapping

from ..contract_primitives import deep_freeze, fingerprint
from .commission_dispute import CommissionDispute
from .commission_reconciliation import CommissionReconciliation
from .commission_settlement import CommissionSettlement
from .financial_domain import (
    FinancialCurrencyMismatchError,
    FinancialTenantScopeError,
    MonetaryAmount,
)


CORE008_COMMISSION_ADJUSTMENT_SCHEMA_VERSION = 1


class CommissionAdjustmentError(ValueError):
    """Base commission adjustment error."""


class CommissionAdjustmentValidationError(
    CommissionAdjustmentError
):
    """Invalid commission adjustment."""


class CommissionAdjustmentType(str, Enum):
    CREDIT = "CREDIT"
    DEBIT = "DEBIT"
    CORRECTION = "CORRECTION"
    REVERSAL = "REVERSAL"


class CommissionAdjustmentState(str, Enum):
    PROPOSED = "PROPOSED"
    APPROVED = "APPROVED"
    APPLIED = "APPLIED"
    REJECTED = "REJECTED"
    VOID = "VOID"


def _text(value: str, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise CommissionAdjustmentValidationError(
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
        raise CommissionAdjustmentValidationError(
            f"{field} must be timezone-aware."
        )

    return value.astimezone(timezone.utc)


def _positive(value: int, field: str) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or value < 1
    ):
        raise CommissionAdjustmentValidationError(
            f"{field} must be a positive integer."
        )
    return value


@dataclass(frozen=True, slots=True)
class CommissionAdjustment:
    """Immutable financial correction instruction.

    This records an approved financial adjustment.
    It does not post to a ledger or execute a payment.
    """

    adjustment_id: str
    tenant_id: str
    commission_id: str
    dispute_id: str
    settlement_id: str
    reconciliation_id: str | None
    adjustment_version: int
    adjustment_type: CommissionAdjustmentType
    amount: MonetaryAmount
    reason_code: str
    authorization_reference: str
    provenance_reference: str
    evidence_reference: str
    effective_at: datetime
    state: CommissionAdjustmentState = (
        CommissionAdjustmentState.PROPOSED
    )
    metadata: Mapping[str, Any] = ()

    def __post_init__(self) -> None:
        for field in (
            "adjustment_id",
            "tenant_id",
            "commission_id",
            "dispute_id",
            "settlement_id",
            "reason_code",
            "authorization_reference",
            "provenance_reference",
            "evidence_reference",
        ):
            object.__setattr__(
                self,
                field,
                _text(
                    getattr(self, field),
                    field,
                ),
            )

        if self.reconciliation_id is not None:
            object.__setattr__(
                self,
                "reconciliation_id",
                _text(
                    self.reconciliation_id,
                    "reconciliation_id",
                ),
            )

        object.__setattr__(
            self,
            "adjustment_version",
            _positive(
                self.adjustment_version,
                "adjustment_version",
            ),
        )

        try:
            adjustment_type = CommissionAdjustmentType(
                self.adjustment_type
            )
            state = CommissionAdjustmentState(
                self.state
            )
        except ValueError as exc:
            raise CommissionAdjustmentValidationError(
                "Unsupported adjustment enum."
            ) from exc

        object.__setattr__(
            self,
            "adjustment_type",
            adjustment_type,
        )
        object.__setattr__(
            self,
            "state",
            state,
        )

        if not isinstance(
            self.amount,
            MonetaryAmount,
        ):
            raise CommissionAdjustmentValidationError(
                "amount must be MonetaryAmount."
            )

        if self.amount.amount <= 0:
            raise CommissionAdjustmentValidationError(
                "adjustment amount must be greater than zero."
            )

        object.__setattr__(
            self,
            "effective_at",
            _aware(
                self.effective_at,
                "effective_at",
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
            raise CommissionAdjustmentValidationError(
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
    def create_from_dispute(
        cls,
        dispute: CommissionDispute,
        settlement: CommissionSettlement,
        *,
        adjustment_id: str,
        adjustment_type: CommissionAdjustmentType,
        amount: MonetaryAmount,
        reason_code: str,
        authorization_reference: str,
        provenance_reference: str,
        evidence_reference: str,
        effective_at: datetime,
        reconciliation: CommissionReconciliation | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> "CommissionAdjustment":
        if not isinstance(
            dispute,
            CommissionDispute,
        ):
            raise CommissionAdjustmentValidationError(
                "dispute must be CommissionDispute."
            )

        if not isinstance(
            settlement,
            CommissionSettlement,
        ):
            raise CommissionAdjustmentValidationError(
                "settlement must be CommissionSettlement."
            )

        if (
            dispute.tenant_id
            != settlement.tenant_id
        ):
            raise CommissionAdjustmentValidationError(
                "Dispute and settlement tenant mismatch."
            )

        if (
            dispute.settlement_id
            != settlement.settlement_id
        ):
            raise CommissionAdjustmentValidationError(
                "Dispute does not reference settlement."
            )

        reconciliation_id = None

        if reconciliation is not None:
            if not isinstance(
                reconciliation,
                CommissionReconciliation,
            ):
                raise CommissionAdjustmentValidationError(
                    "reconciliation must be "
                    "CommissionReconciliation."
                )

            if (
                reconciliation.settlement_id
                != settlement.settlement_id
            ):
                raise CommissionAdjustmentValidationError(
                    "Reconciliation does not reference settlement."
                )

            reconciliation_id = (
                reconciliation.reconciliation_id
            )

        if (
            amount.currency.identity_key
            != settlement.amount.currency.identity_key
        ):
            raise FinancialCurrencyMismatchError(
                "Adjustment currency must match settlement."
            )

        return cls(
            adjustment_id=adjustment_id,
            tenant_id=dispute.tenant_id,
            commission_id=dispute.commission_id,
            dispute_id=dispute.dispute_id,
            settlement_id=settlement.settlement_id,
            reconciliation_id=reconciliation_id,
            adjustment_version=1,
            adjustment_type=adjustment_type,
            amount=amount,
            reason_code=reason_code,
            authorization_reference=authorization_reference,
            provenance_reference=provenance_reference,
            evidence_reference=evidence_reference,
            effective_at=effective_at,
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
            self.adjustment_id,
            self.adjustment_version,
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
                "Commission adjustment crossed tenant scope."
            )

    def approve(
        self,
        *,
        authorization_reference: str,
    ) -> "CommissionAdjustment":
        return CommissionAdjustment(
            adjustment_id=self.adjustment_id,
            tenant_id=self.tenant_id,
            commission_id=self.commission_id,
            dispute_id=self.dispute_id,
            settlement_id=self.settlement_id,
            reconciliation_id=self.reconciliation_id,
            adjustment_version=self.adjustment_version + 1,
            adjustment_type=self.adjustment_type,
            amount=self.amount,
            reason_code=self.reason_code,
            authorization_reference=authorization_reference,
            provenance_reference=self.provenance_reference,
            evidence_reference=self.evidence_reference,
            effective_at=self.effective_at,
            state=CommissionAdjustmentState.APPROVED,
            metadata=self.metadata,
        )

    def mark_applied(self) -> "CommissionAdjustment":
        if self.state is not CommissionAdjustmentState.APPROVED:
            raise CommissionAdjustmentValidationError(
                "Only APPROVED adjustments can be applied."
            )

        return CommissionAdjustment(
            adjustment_id=self.adjustment_id,
            tenant_id=self.tenant_id,
            commission_id=self.commission_id,
            dispute_id=self.dispute_id,
            settlement_id=self.settlement_id,
            reconciliation_id=self.reconciliation_id,
            adjustment_version=self.adjustment_version + 1,
            adjustment_type=self.adjustment_type,
            amount=self.amount,
            reason_code=self.reason_code,
            authorization_reference=self.authorization_reference,
            provenance_reference=self.provenance_reference,
            evidence_reference=self.evidence_reference,
            effective_at=self.effective_at,
            state=CommissionAdjustmentState.APPLIED,
            metadata=self.metadata,
        )

    def to_dict(
        self,
        *,
        include_fingerprint: bool = True,
    ) -> dict[str, Any]:
        result = {
            "source_of_truth": (
                "CORE-008.COMMISSION_ADJUSTMENT"
            ),
            "schema_version": (
                CORE008_COMMISSION_ADJUSTMENT_SCHEMA_VERSION
            ),
            "adjustment_id": self.adjustment_id,
            "tenant_id": self.tenant_id,
            "commission_id": self.commission_id,
            "dispute_id": self.dispute_id,
            "settlement_id": self.settlement_id,
            "reconciliation_id": (
                self.reconciliation_id
            ),
            "adjustment_version": (
                self.adjustment_version
            ),
            "adjustment_type": (
                self.adjustment_type.value
            ),
            "amount": self.amount.to_dict(),
            "reason_code": self.reason_code,
            "authorization_reference": (
                self.authorization_reference
            ),
            "provenance_reference": (
                self.provenance_reference
            ),
            "evidence_reference": (
                self.evidence_reference
            ),
            "effective_at": (
                self.effective_at.isoformat()
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
    "CORE008_COMMISSION_ADJUSTMENT_SCHEMA_VERSION",
    "CommissionAdjustmentError",
    "CommissionAdjustmentValidationError",
    "CommissionAdjustmentType",
    "CommissionAdjustmentState",
    "CommissionAdjustment",
]
