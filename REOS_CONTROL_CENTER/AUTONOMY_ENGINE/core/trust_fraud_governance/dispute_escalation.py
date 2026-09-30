"""CORE-007 T07 — dispute and escalation hooks.

This module models escalation intent only.

It does not:
- decide legal outcomes,
- settle disputes,
- authorize financial actions,
- execute payments,
- create a duplicate case-management engine.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4


class EscalationError(ValueError):
    """Base escalation error."""


class EscalationLevel(str, Enum):
    REVIEW = "REVIEW"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class EscalationState(str, Enum):
    OPEN = "OPEN"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    RESOLVED = "RESOLVED"
    CANCELLED = "CANCELLED"


@dataclass(frozen=True, slots=True)
class EscalationHook:
    hook_id: UUID
    tenant_id: str
    subject_id: str
    correlation_id: str

    level: EscalationLevel
    reason: str
    evidence_references: tuple[str, ...]

    created_at: datetime
    state: EscalationState = EscalationState.OPEN

    def __post_init__(self) -> None:
        if not self.tenant_id or not self.subject_id:
            raise EscalationError(
                "tenant_id and subject_id are required."
            )

        if not self.reason.strip():
            raise EscalationError("reason is required.")

        if not self.evidence_references:
            raise EscalationError(
                "Escalation requires evidence references."
            )

        if (
            self.created_at.tzinfo is None
            or self.created_at.utcoffset() is None
        ):
            raise EscalationError(
                "created_at must be timezone-aware."
            )

        object.__setattr__(
            self,
            "created_at",
            self.created_at.astimezone(timezone.utc),
        )


class EscalationHooks:
    """Creates immutable escalation requests."""

    @staticmethod
    def create(
        *,
        tenant_id: str,
        subject_id: str,
        correlation_id: str,
        level: EscalationLevel,
        reason: str,
        evidence_references: tuple[str, ...],
        created_at: datetime,
        hook_id: UUID | None = None,
    ) -> EscalationHook:
        return EscalationHook(
            hook_id=hook_id or uuid4(),
            tenant_id=tenant_id,
            subject_id=subject_id,
            correlation_id=correlation_id,
            level=level,
            reason=reason,
            evidence_references=tuple(
                sorted(set(evidence_references))
            ),
            created_at=created_at,
        )

    @staticmethod
    def acknowledge(
        hook: EscalationHook,
    ) -> EscalationHook:
        if hook.state is not EscalationState.OPEN:
            raise EscalationError(
                "Only open escalation hooks can be acknowledged."
            )

        return EscalationHook(
            hook_id=hook.hook_id,
            tenant_id=hook.tenant_id,
            subject_id=hook.subject_id,
            correlation_id=hook.correlation_id,
            level=hook.level,
            reason=hook.reason,
            evidence_references=hook.evidence_references,
            created_at=hook.created_at,
            state=EscalationState.ACKNOWLEDGED,
        )

    @staticmethod
    def resolve(
        hook: EscalationHook,
    ) -> EscalationHook:
        if hook.state not in {
            EscalationState.OPEN,
            EscalationState.ACKNOWLEDGED,
        }:
            raise EscalationError(
                "Only open/acknowledged hooks can resolve."
            )

        return EscalationHook(
            hook_id=hook.hook_id,
            tenant_id=hook.tenant_id,
            subject_id=hook.subject_id,
            correlation_id=hook.correlation_id,
            level=hook.level,
            reason=hook.reason,
            evidence_references=hook.evidence_references,
            created_at=hook.created_at,
            state=EscalationState.RESOLVED,
        )
