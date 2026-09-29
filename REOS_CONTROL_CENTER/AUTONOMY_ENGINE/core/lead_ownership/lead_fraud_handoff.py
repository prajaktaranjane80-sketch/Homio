"""
CORE-003 T07 — Duplicate/Fraud Handoff

Purpose:
- Produce a deterministic handoff signal when CORE-003 detects
  a condition that should be reviewed by the future fraud/governance layer.
- Preserve evidence references and observed revisions.
- Support idempotent downstream handling.

This module does NOT make fraud decisions.

It is a handoff contract only.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
import hashlib
import json
from uuid import UUID, uuid4


class FraudHandoffError(Exception):
    """Base fraud handoff error."""


class FraudHandoffValidationError(
    FraudHandoffError
):
    """Invalid fraud handoff data."""


class FraudHandoffConflictError(
    FraudHandoffError
):
    """Conflicting handoff identity."""


class FraudHandoffReason(str, Enum):
    DUPLICATE_LEAD = "DUPLICATE_LEAD"
    ATTRIBUTION_CONFLICT = "ATTRIBUTION_CONFLICT"
    OWNERSHIP_CONFLICT = "OWNERSHIP_CONFLICT"
    IDENTITY_REUSE = "IDENTITY_REUSE"
    EVIDENCE_CONFLICT = "EVIDENCE_CONFLICT"
    SUSPICIOUS_MUTATION = "SUSPICIOUS_MUTATION"


class FraudHandoffPriority(str, Enum):
    INFORMATIONAL = "INFORMATIONAL"
    REVIEW = "REVIEW"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


def _uuid(value: UUID, field_name: str) -> UUID:
    if not isinstance(value, UUID):
        raise FraudHandoffValidationError(
            f"{field_name} must be UUID"
        )
    return value


def _text(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise FraudHandoffValidationError(
            f"{field_name} must be non-empty text"
        )
    return value.strip()


def _time(value: datetime, field_name: str) -> datetime:
    if not isinstance(value, datetime):
        raise FraudHandoffValidationError(
            f"{field_name} must be datetime"
        )

    if value.tzinfo is None or value.utcoffset() is None:
        raise FraudHandoffValidationError(
            f"{field_name} must be timezone-aware"
        )

    return value.astimezone(timezone.utc)


@dataclass(frozen=True, slots=True)
class LeadFraudHandoff:
    handoff_id: UUID
    tenant_id: UUID
    lead_id: UUID
    reason: FraudHandoffReason
    priority: FraudHandoffPriority
    idempotency_key: str
    evidence_references: tuple[str, ...]
    source_reference: str
    observed_lead_revision: int | None
    observed_ownership_revision: int | None
    created_at: datetime

    def __post_init__(self) -> None:
        _uuid(self.handoff_id, "handoff_id")
        _uuid(self.tenant_id, "tenant_id")
        _uuid(self.lead_id, "lead_id")

        if not isinstance(
            self.reason,
            FraudHandoffReason,
        ):
            raise FraudHandoffValidationError(
                "reason must be FraudHandoffReason"
            )

        if not isinstance(
            self.priority,
            FraudHandoffPriority,
        ):
            raise FraudHandoffValidationError(
                "priority must be FraudHandoffPriority"
            )

        object.__setattr__(
            self,
            "idempotency_key",
            _text(
                self.idempotency_key,
                "idempotency_key",
            ),
        )

        if not self.evidence_references:
            raise FraudHandoffValidationError(
                "At least one evidence reference is required"
            )

        normalized = tuple(
            dict.fromkeys(
                _text(
                    reference,
                    "evidence_reference",
                )
                for reference in self.evidence_references
            )
        )

        object.__setattr__(
            self,
            "evidence_references",
            normalized,
        )

        object.__setattr__(
            self,
            "source_reference",
            _text(
                self.source_reference,
                "source_reference",
            ),
        )

        if (
            self.observed_lead_revision is not None
            and (
                not isinstance(
                    self.observed_lead_revision,
                    int,
                )
                or self.observed_lead_revision < 0
            )
        ):
            raise FraudHandoffValidationError(
                "observed_lead_revision must be non-negative integer"
            )

        if (
            self.observed_ownership_revision is not None
            and (
                not isinstance(
                    self.observed_ownership_revision,
                    int,
                )
                or self.observed_ownership_revision < 0
            )
        ):
            raise FraudHandoffValidationError(
                "observed_ownership_revision must be non-negative integer"
            )

        object.__setattr__(
            self,
            "created_at",
            _time(self.created_at, "created_at"),
        )

    @classmethod
    def create(
        cls,
        *,
        tenant_id: UUID,
        lead_id: UUID,
        reason: FraudHandoffReason,
        priority: FraudHandoffPriority,
        idempotency_key: str,
        evidence_references: tuple[str, ...],
        source_reference: str,
        observed_lead_revision: int | None = None,
        observed_ownership_revision: int | None = None,
        handoff_id: UUID | None = None,
        created_at: datetime | None = None,
    ) -> "LeadFraudHandoff":
        return cls(
            handoff_id=handoff_id or uuid4(),
            tenant_id=tenant_id,
            lead_id=lead_id,
            reason=reason,
            priority=priority,
            idempotency_key=idempotency_key,
            evidence_references=evidence_references,
            source_reference=source_reference,
            observed_lead_revision=observed_lead_revision,
            observed_ownership_revision=observed_ownership_revision,
            created_at=(
                created_at
                or datetime.now(timezone.utc)
            ),
        )

    @property
    def handoff_key(self) -> tuple[UUID, UUID, str]:
        return (
            self.tenant_id,
            self.lead_id,
            self.idempotency_key,
        )

    @property
    def fingerprint(self) -> str:
        payload = {
            "tenant_id": str(self.tenant_id),
            "lead_id": str(self.lead_id),
            "reason": self.reason.value,
            "priority": self.priority.value,
            "idempotency_key": self.idempotency_key,
            "evidence_references": self.evidence_references,
            "source_reference": self.source_reference,
            "observed_lead_revision": self.observed_lead_revision,
            "observed_ownership_revision": (
                self.observed_ownership_revision
            ),
            "created_at": self.created_at.isoformat(),
        }

        canonical = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
        )

        return hashlib.sha256(
            canonical.encode("utf-8")
        ).hexdigest()

    def ensure_tenant(self, tenant_id: UUID) -> None:
        _uuid(tenant_id, "tenant_id")

        if tenant_id != self.tenant_id:
            raise FraudHandoffValidationError(
                "Fraud handoff tenant violation"
            )

    def assert_compatible(
        self,
        other: "LeadFraudHandoff",
    ) -> None:
        if not isinstance(
            other,
            LeadFraudHandoff,
        ):
            raise FraudHandoffValidationError(
                "other must be LeadFraudHandoff"
            )

        if self.handoff_key != other.handoff_key:
            raise FraudHandoffConflictError(
                "Handoff identities differ"
            )

        if self.fingerprint != other.fingerprint:
            raise FraudHandoffConflictError(
                "Same idempotency key has conflicting payload"
            )

    def to_dict(self) -> dict[str, object]:
        return {
            "handoff_id": str(self.handoff_id),
            "tenant_id": str(self.tenant_id),
            "lead_id": str(self.lead_id),
            "reason": self.reason.value,
            "priority": self.priority.value,
            "idempotency_key": self.idempotency_key,
            "evidence_references": list(
                self.evidence_references
            ),
            "source_reference": self.source_reference,
            "observed_lead_revision": (
                self.observed_lead_revision
            ),
            "observed_ownership_revision": (
                self.observed_ownership_revision
            ),
            "created_at": self.created_at.isoformat(),
            "fingerprint": self.fingerprint,
        }
