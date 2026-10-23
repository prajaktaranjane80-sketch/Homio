from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Mapping

from ..contract_primitives import deep_freeze, fingerprint
from .commission_dispute import (
    CommissionDispute,
    CommissionDisputeResolution,
    CommissionDisputeState,
)
from .commission_reconciliation import (
    CommissionReconciliation,
    CommissionReconciliationState,
)
from .commission_settlement import (
    CommissionSettlement,
    CommissionSettlementState,
)
from .commission_security import (
    FinancialAuthorizationAction,
    FinancialAuthorizationRequest,
    FinancialSecurityBoundary,
)
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


def _merge_reserved_audit_metadata(
    metadata: Mapping[str, Any],
    additions: Mapping[str, Any],
) -> dict[str, Any]:
    result = dict(metadata)

    for key, value in additions.items():
        if key in result and result[key] != value:
            raise CommissionAdjustmentValidationError(
                f"metadata cannot override reserved audit field: {key}"
            )

        result[key] = value

    return result


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
        except (TypeError, ValueError) as exc:
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
        if not isinstance(dispute, CommissionDispute):
            raise CommissionAdjustmentValidationError(
                "dispute must be CommissionDispute."
            )

        if not isinstance(settlement, CommissionSettlement):
            raise CommissionAdjustmentValidationError(
                "settlement must be CommissionSettlement."
            )

        if not isinstance(amount, MonetaryAmount):
            raise CommissionAdjustmentValidationError(
                "amount must be MonetaryAmount."
            )

        try:
            resolved_type = CommissionAdjustmentType(
                adjustment_type
            )
        except (TypeError, ValueError) as exc:
            raise CommissionAdjustmentValidationError(
                "Unsupported adjustment type."
            ) from exc

        if (
            dispute.state is not CommissionDisputeState.RESOLVED
            or dispute.resolution
            not in {
                CommissionDisputeResolution.ACCEPTED,
                CommissionDisputeResolution.PARTIALLY_ACCEPTED,
            }
        ):
            raise CommissionAdjustmentValidationError(
                "An adjustment requires a resolved, accepted dispute."
            )

        if dispute.tenant_id != settlement.tenant_id:
            raise CommissionAdjustmentValidationError(
                "Dispute and settlement tenant mismatch."
            )

        if dispute.commission_id != settlement.commission_id:
            raise CommissionAdjustmentValidationError(
                "Dispute and settlement commission mismatch."
            )

        if dispute.settlement_id != settlement.settlement_id:
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
                    "reconciliation must be CommissionReconciliation."
                )

            if (
                reconciliation.tenant_id != settlement.tenant_id
                or reconciliation.commission_id != settlement.commission_id
            ):
                raise CommissionAdjustmentValidationError(
                    "Reconciliation tenant or commission mismatch."
                )

            if reconciliation.settlement_id != settlement.settlement_id:
                raise CommissionAdjustmentValidationError(
                    "Reconciliation does not reference settlement."
                )

            if (
                dispute.reconciliation_id is not None
                and dispute.reconciliation_id
                != reconciliation.reconciliation_id
            ):
                raise CommissionAdjustmentValidationError(
                    "Reconciliation does not match the dispute."
                )

            reconciliation_id = reconciliation.reconciliation_id

        if (
            amount.currency.identity_key
            != settlement.amount.currency.identity_key
        ):
            raise FinancialCurrencyMismatchError(
                "Adjustment currency must match settlement."
            )

        if amount.amount > settlement.amount.amount:
            raise CommissionAdjustmentValidationError(
                "Adjustment amount cannot exceed settlement amount."
            )

        if (
            dispute.disputed_amount is not None
            and amount.amount > dispute.disputed_amount.amount
        ):
            raise CommissionAdjustmentValidationError(
                "Adjustment amount cannot exceed disputed amount."
            )

        if resolved_type is CommissionAdjustmentType.REVERSAL:
            if settlement.state is not CommissionSettlementState.CONFIRMED:
                raise CommissionAdjustmentValidationError(
                    "A reversal requires a confirmed settlement."
                )

            if (
                reconciliation is None
                or reconciliation.state
                is not CommissionReconciliationState.MATCHED
            ):
                raise CommissionAdjustmentValidationError(
                    "A reversal requires its matching reconciliation."
                )

        return cls(
            adjustment_id=adjustment_id,
            tenant_id=dispute.tenant_id,
            commission_id=dispute.commission_id,
            dispute_id=dispute.dispute_id,
            settlement_id=settlement.settlement_id,
            reconciliation_id=reconciliation_id,
            adjustment_version=1,
            adjustment_type=resolved_type,
            amount=amount,
            reason_code=reason_code,
            authorization_reference=authorization_reference,
            provenance_reference=provenance_reference,
            evidence_reference=evidence_reference,
            effective_at=effective_at,
            metadata={} if metadata is None else metadata,
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
        authorization_boundary: FinancialSecurityBoundary,
        actor_reference: str,
        authorization_reference: str,
        approved_at: datetime,
    ) -> "CommissionAdjustment":
        if self.state is not CommissionAdjustmentState.PROPOSED:
            raise CommissionAdjustmentValidationError(
                "Only PROPOSED adjustments can be approved."
            )

        if not isinstance(
            authorization_boundary,
            FinancialSecurityBoundary,
        ):
            raise CommissionAdjustmentValidationError(
                "authorization_boundary must be FinancialSecurityBoundary."
            )

        actor = _text(actor_reference, "actor_reference")
        authorization_ref = _text(
            authorization_reference,
            "authorization_reference",
        )
        approved_time = _aware(approved_at, "approved_at")
        source_fingerprint = self.immutable_fingerprint

        audit_metadata = _merge_reserved_audit_metadata(
            self.metadata,
            {
                "approval_source_fingerprint": source_fingerprint,
                "approved_actor_reference": actor,
                "approved_at": approved_time.isoformat(),
                "approval_authorization_reference": authorization_ref,
                "approval_operation": "APPROVE_ADJUSTMENT",
            },
        )

        context = {
            "operation": "APPROVE_ADJUSTMENT",
            "adjustment_id": self.adjustment_id,
            "adjustment_version": self.adjustment_version,
            "adjustment_fingerprint": source_fingerprint,
            "adjustment_type": self.adjustment_type.value,
            "amount": self.amount.to_dict(),
            "dispute_id": self.dispute_id,
            "settlement_id": self.settlement_id,
            "reconciliation_id": self.reconciliation_id,
            "provenance_reference": self.provenance_reference,
            "evidence_reference": self.evidence_reference,
            "effective_at": self.effective_at.isoformat(),
            "approved_at": approved_time.isoformat(),
        }

        authorization_boundary.authorize(
            FinancialAuthorizationRequest(
                tenant_id=self.tenant_id,
                resource_tenant_id=self.tenant_id,
                actor_reference=actor,
                resource_reference=self.adjustment_id,
                action=FinancialAuthorizationAction.ADJUST,
                authorization_reference=authorization_ref,
                sensitive=True,
                context=context,
            )
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
            authorization_reference=authorization_ref,
            provenance_reference=self.provenance_reference,
            evidence_reference=self.evidence_reference,
            effective_at=self.effective_at,
            state=CommissionAdjustmentState.APPROVED,
            metadata=audit_metadata,
        )

    def mark_applied(
        self,
        *,
        authorization_boundary: FinancialSecurityBoundary,
        actor_reference: str,
        authorization_reference: str,
        applied_at: datetime,
    ) -> "CommissionAdjustment":
        if self.state is not CommissionAdjustmentState.APPROVED:
            raise CommissionAdjustmentValidationError(
                "Only APPROVED adjustments can be applied."
            )

        if not isinstance(
            authorization_boundary,
            FinancialSecurityBoundary,
        ):
            raise CommissionAdjustmentValidationError(
                "authorization_boundary must be FinancialSecurityBoundary."
            )

        approval_source_fingerprint = self.metadata.get(
            "approval_source_fingerprint"
        )
        approved_actor = self.metadata.get(
            "approved_actor_reference"
        )
        approved_at_value = self.metadata.get("approved_at")
        approval_reference = self.metadata.get(
            "approval_authorization_reference"
        )

        if not all(
            isinstance(value, str) and value.strip()
            for value in (
                approval_source_fingerprint,
                approved_actor,
                approved_at_value,
                approval_reference,
            )
        ):
            raise CommissionAdjustmentValidationError(
                "Approved adjustment is missing its authorization audit linkage."
            )

        try:
            approved_time = _aware(
                datetime.fromisoformat(approved_at_value),
                "approved_at",
            )
        except (TypeError, ValueError) as exc:
            raise CommissionAdjustmentValidationError(
                "Approved adjustment has an invalid approved_at audit value."
            ) from exc

        actor = _text(actor_reference, "actor_reference")
        authorization_ref = _text(
            authorization_reference,
            "authorization_reference",
        )
        applied_time = _aware(applied_at, "applied_at")

        if applied_time < approved_time:
            raise CommissionAdjustmentValidationError(
                "Adjustment cannot be applied before approval."
            )

        if applied_time < self.effective_at:
            raise CommissionAdjustmentValidationError(
                "Adjustment cannot be applied before its effective_at time."
            )

        approved_fingerprint = self.immutable_fingerprint

        audit_metadata = _merge_reserved_audit_metadata(
            self.metadata,
            {
                "application_source_fingerprint": approved_fingerprint,
                "applied_actor_reference": actor,
                "applied_at": applied_time.isoformat(),
                "application_authorization_reference": authorization_ref,
                "application_operation": "APPLY_ADJUSTMENT",
            },
        )

        context = {
            "operation": "APPLY_ADJUSTMENT",
            "adjustment_id": self.adjustment_id,
            "adjustment_version": self.adjustment_version,
            "adjustment_fingerprint": approved_fingerprint,
            "approval_source_fingerprint": approval_source_fingerprint,
            "approval_authorization_reference": approval_reference,
            "approved_actor_reference": approved_actor,
            "approved_at": approved_time.isoformat(),
            "adjustment_type": self.adjustment_type.value,
            "amount": self.amount.to_dict(),
            "dispute_id": self.dispute_id,
            "settlement_id": self.settlement_id,
            "reconciliation_id": self.reconciliation_id,
            "applied_at": applied_time.isoformat(),
        }

        authorization_boundary.authorize(
            FinancialAuthorizationRequest(
                tenant_id=self.tenant_id,
                resource_tenant_id=self.tenant_id,
                actor_reference=actor,
                resource_reference=self.adjustment_id,
                action=FinancialAuthorizationAction.ADJUST,
                authorization_reference=authorization_ref,
                sensitive=True,
                context=context,
            )
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
            authorization_reference=authorization_ref,
            provenance_reference=self.provenance_reference,
            evidence_reference=self.evidence_reference,
            effective_at=self.effective_at,
            state=CommissionAdjustmentState.APPLIED,
            metadata=audit_metadata,
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
