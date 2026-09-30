"""CORE-007 T05 — controlled approval workflow.

This is a workflow contract, not a replacement authorization engine.

Authorization remains owned by the identity/authority layer.
Governance decides when approval is required.
This module records the immutable workflow decision/evidence.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
import hashlib
import json
from typing import Any
from uuid import UUID, uuid4


class ApprovalWorkflowError(ValueError):
    """Base approval workflow error."""


class ApprovalTransitionError(
    ApprovalWorkflowError
):
    """Invalid approval transition."""


class ApprovalState(str, Enum):
    NOT_REQUIRED = "NOT_REQUIRED"
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"


class ApprovalDecision(str, Enum):
    APPROVE = "APPROVE"
    REJECT = "REJECT"


_ALLOWED = {
    ApprovalState.PENDING: {
        ApprovalState.APPROVED,
        ApprovalState.REJECTED,
        ApprovalState.EXPIRED,
        ApprovalState.CANCELLED,
    }
}


def _utc(value: datetime, field: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ApprovalWorkflowError(
            f"{field} must be timezone-aware."
        )
    return value.astimezone(timezone.utc)


@dataclass(frozen=True, slots=True)
class ApprovalRequest:
    """Immutable approval request."""

    request_id: UUID
    tenant_id: str
    subject_id: str
    correlation_id: str

    governance_fingerprint: str
    policy_id: str
    policy_version: str

    requested_at: datetime
    expires_at: datetime

    state: ApprovalState = ApprovalState.PENDING

    def __post_init__(self) -> None:
        requested = _utc(
            self.requested_at,
            "requested_at",
        )
        expires = _utc(
            self.expires_at,
            "expires_at",
        )

        if expires <= requested:
            raise ApprovalWorkflowError(
                "expires_at must be after requested_at."
            )

        object.__setattr__(
            self,
            "requested_at",
            requested,
        )
        object.__setattr__(
            self,
            "expires_at",
            expires,
        )

        if not self.tenant_id or not self.subject_id:
            raise ApprovalWorkflowError(
                "tenant_id and subject_id are required."
            )

    @property
    def fingerprint(self) -> str:
        payload = {
            "request_id": str(self.request_id),
            "tenant_id": self.tenant_id,
            "subject_id": self.subject_id,
            "correlation_id": self.correlation_id,
            "governance_fingerprint": (
                self.governance_fingerprint
            ),
            "policy_id": self.policy_id,
            "policy_version": self.policy_version,
            "requested_at": self.requested_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "state": self.state.value,
        }

        raw = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")

        return hashlib.sha256(raw).hexdigest()


@dataclass(frozen=True, slots=True)
class ApprovalRecord:
    """Immutable approval transition result."""

    request_id: UUID
    state: ApprovalState
    decision_at: datetime
    actor_reference: str
    reason: str
    fingerprint: str

    @classmethod
    def create(
        cls,
        *,
        request: ApprovalRequest,
        state: ApprovalState,
        actor_reference: str,
        reason: str,
        decision_at: datetime,
    ) -> "ApprovalRecord":
        if state not in {
            ApprovalState.APPROVED,
            ApprovalState.REJECTED,
            ApprovalState.EXPIRED,
            ApprovalState.CANCELLED,
        }:
            raise ApprovalTransitionError(
                "Approval record requires terminal state."
            )

        timestamp = _utc(
            decision_at,
            "decision_at",
        )

        payload = {
            "request_id": str(request.request_id),
            "state": state.value,
            "decision_at": timestamp.isoformat(),
            "actor_reference": actor_reference,
            "reason": reason,
            "request_fingerprint": request.fingerprint,
        }

        raw = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")

        fingerprint = hashlib.sha256(raw).hexdigest()

        return cls(
            request_id=request.request_id,
            state=state,
            decision_at=timestamp,
            actor_reference=actor_reference,
            reason=reason,
            fingerprint=fingerprint,
        )


class ApprovalWorkflow:
    """Creates controlled approval requests and transitions."""

    @staticmethod
    def request(
        *,
        tenant_id: str,
        subject_id: str,
        correlation_id: str,
        governance_fingerprint: str,
        policy_id: str,
        policy_version: str,
        requested_at: datetime,
        expires_at: datetime,
        request_id: UUID | None = None,
    ) -> ApprovalRequest:
        return ApprovalRequest(
            request_id=request_id or uuid4(),
            tenant_id=tenant_id,
            subject_id=subject_id,
            correlation_id=correlation_id,
            governance_fingerprint=governance_fingerprint,
            policy_id=policy_id,
            policy_version=policy_version,
            requested_at=requested_at,
            expires_at=expires_at,
        )

    @staticmethod
    def transition(
        *,
        request: ApprovalRequest,
        decision: ApprovalDecision,
        actor_reference: str,
        reason: str,
        decision_at: datetime,
    ) -> ApprovalRecord:
        if request.state is not ApprovalState.PENDING:
            raise ApprovalTransitionError(
                "Only pending requests can transition."
            )

        if not actor_reference.strip():
            raise ApprovalWorkflowError(
                "actor_reference is required."
            )

        target_state = (
            ApprovalState.APPROVED
            if decision is ApprovalDecision.APPROVE
            else ApprovalState.REJECTED
        )

        return ApprovalRecord.create(
            request=request,
            state=target_state,
            actor_reference=actor_reference,
            reason=reason,
            decision_at=decision_at,
        )

    @staticmethod
    def expire(
        *,
        request: ApprovalRequest,
        at: datetime,
    ) -> ApprovalRecord:
        timestamp = _utc(at, "at")

        if timestamp < request.expires_at:
            raise ApprovalTransitionError(
                "Approval request has not expired."
            )

        return ApprovalRecord.create(
            request=request,
            state=ApprovalState.EXPIRED,
            actor_reference="SYSTEM:EXPIRATION",
            reason="Approval request expired.",
            decision_at=timestamp,
        )
