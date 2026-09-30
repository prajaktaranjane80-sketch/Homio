from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Mapping

from ..contract_primitives import deep_freeze, fingerprint
from .commission_reconciliation import CommissionReconciliation
from .commission_settlement import CommissionSettlement
from .financial_domain import (
    FinancialTenantScopeError,
    MonetaryAmount,
)


CORE008_COMMISSION_DISPUTE_SCHEMA_VERSION = 1


class CommissionDisputeError(ValueError):
    """Base commission dispute error."""


class CommissionDisputeValidationError(
    CommissionDisputeError
):
    """Invalid commission dispute."""


class CommissionDisputeState(str, Enum):
    OPEN = "OPEN"
    UNDER_REVIEW = "UNDER_REVIEW"
    EVIDENCE_REQUIRED = "EVIDENCE_REQUIRED"
    RESOLVED = "RESOLVED"
    REJECTED = "REJECTED"
    WITHDRAWN = "WITHDRAWN"
    ESCALATED = "ESCALATED"


class CommissionDisputeType(str, Enum):
    AMOUNT = "AMOUNT"
    ENTITLEMENT = "ENTITLEMENT"
    ALLOCATION = "ALLOCATION"
    SETTLEMENT = "SETTLEMENT"
    RECONCILIATION = "RECONCILIATION"
    CONTRACT = "CONTRACT"
    DUPLICATE = "DUPLICATE"
    OTHER = "OTHER"


class CommissionDisputeResolution(str, Enum):
    NONE = "NONE"
    ACCEPTED = "ACCEPTED"
    PARTIALLY_ACCEPTED = "PARTIALLY_ACCEPTED"
    REJECTED = "REJECTED"
    SUPERSEDED = "SUPERSEDED"


def _text(value: str, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise CommissionDisputeValidationError(
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
        raise CommissionDisputeValidationError(
            f"{field} must be timezone-aware."
        )

    return value.astimezone(timezone.utc)


def _positive(value: int, field: str) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or value < 1
    ):
        raise CommissionDisputeValidationError(
            f"{field} must be a positive integer."
        )

    return value


@dataclass(frozen=True, slots=True)
class CommissionDispute:
    """Immutable financial dispute case.

    CORE-008 owns financial dispute identity and references.
    CORE-007 remains the authority for trust/fraud/governance decisions.
    """

    dispute_id: str
    tenant_id: str
    commission_id: str
    settlement_id: str
    reconciliation_id: str | None
    dispute_version: int
    dispute_type: CommissionDisputeType
    claimant_reference: str
    disputed_amount: MonetaryAmount | None
    reason_code: str
    description: str
    evidence_reference: str
    authorization_reference: str
    provenance_reference: str
    opened_at: datetime
    state: CommissionDisputeState = (
        CommissionDisputeState.OPEN
    )
    resolution: CommissionDisputeResolution = (
        CommissionDisputeResolution.NONE
    )
    resolution_reference: str | None = None
    metadata: Mapping[str, Any] = ()

    def __post_init__(self) -> None:
        for field in (
            "dispute_id",
            "tenant_id",
            "commission_id",
            "settlement_id",
            "claimant_reference",
            "reason_code",
            "description",
            "evidence_reference",
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
            "dispute_version",
            _positive(
                self.dispute_version,
                "dispute_version",
            ),
        )

        try:
            dispute_type = CommissionDisputeType(
                self.dispute_type
            )
            state = CommissionDisputeState(
                self.state
            )
            resolution = CommissionDisputeResolution(
                self.resolution
            )
        except ValueError as exc:
            raise CommissionDisputeValidationError(
                "Unsupported dispute enum."
            ) from exc

        object.__setattr__(
            self,
            "dispute_type",
            dispute_type,
        )
        object.__setattr__(
            self,
            "state",
            state,
        )
        object.__setattr__(
            self,
            "resolution",
            resolution,
        )

        if self.disputed_amount is not None:
            if not isinstance(
                self.disputed_amount,
                MonetaryAmount,
            ):
                raise CommissionDisputeValidationError(
                    "disputed_amount must be MonetaryAmount."
                )

            if self.disputed_amount.amount < 0:
                raise CommissionDisputeValidationError(
                    "disputed_amount cannot be negative."
                )

        object.__setattr__(
            self,
            "opened_at",
            _aware(
                self.opened_at,
                "opened_at",
            ),
        )

        if self.resolution_reference is not None:
            object.__setattr__(
                self,
                "resolution_reference",
                _text(
                    self.resolution_reference,
                    "resolution_reference",
                ),
            )

        if (
            self.resolution is not CommissionDisputeResolution.NONE
            and not self.resolution_reference
        ):
            raise CommissionDisputeValidationError(
                "Resolved dispute requires "
                "resolution_reference."
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
            raise CommissionDisputeValidationError(
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
    def open_from_settlement(
        cls,
        settlement: CommissionSettlement,
        *,
        dispute_id: str,
        claimant_reference: str,
        dispute_type: CommissionDisputeType,
        reason_code: str,
        description: str,
        evidence_reference: str,
        authorization_reference: str,
        provenance_reference: str,
        opened_at: datetime,
        disputed_amount: MonetaryAmount | None = None,
        reconciliation: CommissionReconciliation | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> "CommissionDispute":
        if not isinstance(
            settlement,
            CommissionSettlement,
        ):
            raise CommissionDisputeValidationError(
                "settlement must be CommissionSettlement."
            )

        reconciliation_id = None

        if reconciliation is not None:
            if not isinstance(
                reconciliation,
                CommissionReconciliation,
            ):
                raise CommissionDisputeValidationError(
                    "reconciliation must be "
                    "CommissionReconciliation."
                )

            if (
                reconciliation.tenant_id
                != settlement.tenant_id
            ):
                raise CommissionDisputeValidationError(
                    "Settlement and reconciliation "
                    "tenant mismatch."
                )

            if (
                reconciliation.settlement_id
                != settlement.settlement_id
            ):
                raise CommissionDisputeValidationError(
                    "Reconciliation does not reference "
                    "the supplied settlement."
                )

            reconciliation_id = (
                reconciliation.reconciliation_id
            )

        if disputed_amount is not None:
            if (
                disputed_amount.currency.identity_key
                != settlement.amount.currency.identity_key
            ):
                raise CommissionDisputeValidationError(
                    "Disputed amount currency must match settlement."
                )

            if (
                disputed_amount.amount
                > settlement.amount.amount
            ):
                raise CommissionDisputeValidationError(
                    "Disputed amount cannot exceed settlement amount."
                )

        return cls(
            dispute_id=dispute_id,
            tenant_id=settlement.tenant_id,
            commission_id=settlement.commission_id,
            settlement_id=settlement.settlement_id,
            reconciliation_id=reconciliation_id,
            dispute_version=1,
            dispute_type=dispute_type,
            claimant_reference=claimant_reference,
            disputed_amount=disputed_amount,
            reason_code=reason_code,
            description=description,
            evidence_reference=evidence_reference,
            authorization_reference=authorization_reference,
            provenance_reference=provenance_reference,
            opened_at=opened_at,
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
            self.dispute_id,
            self.dispute_version,
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
                "Commission dispute crossed tenant scope."
            )

    def resolve(
        self,
        *,
        resolution: CommissionDisputeResolution,
        resolution_reference: str,
        state: CommissionDisputeState = (
            CommissionDisputeState.RESOLVED
        ),
    ) -> "CommissionDispute":
        resolved_state = CommissionDisputeState(
            state
        )
        resolved_resolution = CommissionDisputeResolution(
            resolution
        )

        if (
            resolved_resolution
            is CommissionDisputeResolution.NONE
        ):
            raise CommissionDisputeValidationError(
                "A resolution cannot be NONE."
            )

        return CommissionDispute(
            dispute_id=self.dispute_id,
            tenant_id=self.tenant_id,
            commission_id=self.commission_id,
            settlement_id=self.settlement_id,
            reconciliation_id=self.reconciliation_id,
            dispute_version=self.dispute_version + 1,
            dispute_type=self.dispute_type,
            claimant_reference=self.claimant_reference,
            disputed_amount=self.disputed_amount,
            reason_code=self.reason_code,
            description=self.description,
            evidence_reference=self.evidence_reference,
            authorization_reference=self.authorization_reference,
            provenance_reference=self.provenance_reference,
            opened_at=self.opened_at,
            state=resolved_state,
            resolution=resolved_resolution,
            resolution_reference=resolution_reference,
            metadata=self.metadata,
        )

    def to_dict(
        self,
        *,
        include_fingerprint: bool = True,
    ) -> dict[str, Any]:
        result = {
            "source_of_truth": (
                "CORE-008.COMMISSION_DISPUTE"
            ),
            "schema_version": (
                CORE008_COMMISSION_DISPUTE_SCHEMA_VERSION
            ),
            "dispute_id": self.dispute_id,
            "tenant_id": self.tenant_id,
            "commission_id": self.commission_id,
            "settlement_id": self.settlement_id,
            "reconciliation_id": self.reconciliation_id,
            "dispute_version": self.dispute_version,
            "dispute_type": self.dispute_type.value,
            "claimant_reference": (
                self.claimant_reference
            ),
            "disputed_amount": (
                self.disputed_amount.to_dict()
                if self.disputed_amount is not None
                else None
            ),
            "reason_code": self.reason_code,
            "description": self.description,
            "evidence_reference": (
                self.evidence_reference
            ),
            "authorization_reference": (
                self.authorization_reference
            ),
            "provenance_reference": (
                self.provenance_reference
            ),
            "opened_at": self.opened_at.isoformat(),
            "state": self.state.value,
            "resolution": self.resolution.value,
            "resolution_reference": (
                self.resolution_reference
            ),
            "metadata": dict(self.metadata),
        }

        if include_fingerprint:
            result["immutable_fingerprint"] = (
                self.immutable_fingerprint
            )

        return result


__all__ = [
    "CORE008_COMMISSION_DISPUTE_SCHEMA_VERSION",
    "CommissionDisputeError",
    "CommissionDisputeValidationError",
    "CommissionDisputeState",
    "CommissionDisputeType",
    "CommissionDisputeResolution",
    "CommissionDispute",
]
