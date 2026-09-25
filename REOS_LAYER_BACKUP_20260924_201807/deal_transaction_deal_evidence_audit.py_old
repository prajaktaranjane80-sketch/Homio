from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Mapping
from uuid import uuid4


class DealEvidenceAuditError(ValueError):
    """Base error for deal evidence/audit integration."""


class DealEvidenceConflictError(DealEvidenceAuditError):
    """Raised when an evidence ID is reused with different immutable data."""


class DealAuditConflictError(DealEvidenceAuditError):
    """Raised when an audit ID is reused with different immutable data."""


class DealEvidenceScopeError(DealEvidenceAuditError):
    """Raised when evidence does not belong to the deal/tenant scope."""


class DealAuditScopeError(DealEvidenceAuditError):
    """Raised when audit data does not belong to the deal/tenant scope."""


@dataclass(frozen=True)
class DealEvidenceReference:
    """Immutable reference to externally governed deal evidence.

    This object does not own evidence files. ARCH-014 remains the evidence
    authority. Deal stores only the immutable reference needed for traceability.
    """

    evidence_id: str
    deal_id: str
    tenant_id: str
    evidence_type: str
    reference: str
    created_at: str
    version: int = 1
    metadata: Mapping[str, Any] = field(default_factory=dict)
    source_of_truth: str = "evidence"

    def __post_init__(self) -> None:
        if not self.evidence_id.strip():
            raise DealEvidenceAuditError("evidence_id is required.")
        if not self.deal_id.strip():
            raise DealEvidenceAuditError("deal_id is required.")
        if not self.tenant_id.strip():
            raise DealEvidenceAuditError("tenant_id is required.")
        if not self.evidence_type.strip():
            raise DealEvidenceAuditError("evidence_type is required.")
        if not self.reference.strip():
            raise DealEvidenceAuditError("reference is required.")
        if self.version < 1:
            raise DealEvidenceAuditError("version must be >= 1.")

    @classmethod
    def create(
        cls,
        *,
        evidence_id: str | None = None,
        deal_id: str,
        tenant_id: str,
        evidence_type: str,
        reference: str,
        created_at: str | None = None,
        version: int = 1,
        metadata: Mapping[str, Any] | None = None,
    ) -> "DealEvidenceReference":
        timestamp = created_at or datetime.now(timezone.utc).isoformat(
            timespec="seconds"
        )

        return cls(
            evidence_id=evidence_id or str(uuid4()),
            deal_id=deal_id,
            tenant_id=tenant_id,
            evidence_type=evidence_type,
            reference=reference,
            created_at=timestamp,
            version=version,
            metadata=dict(metadata or {}),
        )

    def assert_scope(self, *, deal_id: str, tenant_id: str) -> None:
        if self.deal_id != deal_id:
            raise DealEvidenceScopeError(
                "Evidence belongs to a different deal."
            )
        if self.tenant_id != tenant_id:
            raise DealEvidenceScopeError(
                "Evidence belongs to a different tenant."
            )

    def semantic_key(self) -> tuple[Any, ...]:
        return (
            self.evidence_id,
            self.deal_id,
            self.tenant_id,
            self.evidence_type,
            self.reference,
            dict(self.metadata),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "evidence_id": self.evidence_id,
            "deal_id": self.deal_id,
            "tenant_id": self.tenant_id,
            "evidence_type": self.evidence_type,
            "reference": self.reference,
            "created_at": self.created_at,
            "version": self.version,
            "metadata": dict(self.metadata),
            "source_of_truth": self.source_of_truth,
        }


@dataclass(frozen=True)
class DealAuditEntry:
    """Immutable deal audit reference.

    This is a domain-level historical record. It is not a replacement for the
    platform governance/audit authority.
    """

    audit_id: str
    deal_id: str
    tenant_id: str
    action: str
    actor_id: str
    created_at: str
    details: Mapping[str, Any] = field(default_factory=dict)
    version: int = 1
    source_of_truth: str = "deal_audit"

    def __post_init__(self) -> None:
        if not self.audit_id.strip():
            raise DealEvidenceAuditError("audit_id is required.")
        if not self.deal_id.strip():
            raise DealEvidenceAuditError("deal_id is required.")
        if not self.tenant_id.strip():
            raise DealEvidenceAuditError("tenant_id is required.")
        if not self.action.strip():
            raise DealEvidenceAuditError("action is required.")
        if not self.actor_id.strip():
            raise DealEvidenceAuditError("actor_id is required.")
        if self.version < 1:
            raise DealEvidenceAuditError("version must be >= 1.")

    @classmethod
    def create(
        cls,
        *,
        audit_id: str | None = None,
        deal_id: str,
        tenant_id: str,
        action: str,
        actor_id: str,
        created_at: str | None = None,
        details: Mapping[str, Any] | None = None,
        version: int = 1,
    ) -> "DealAuditEntry":
        timestamp = created_at or datetime.now(timezone.utc).isoformat(
            timespec="seconds"
        )

        return cls(
            audit_id=audit_id or str(uuid4()),
            deal_id=deal_id,
            tenant_id=tenant_id,
            action=action,
            actor_id=actor_id,
            created_at=timestamp,
            details=dict(details or {}),
            version=version,
        )

    def assert_scope(self, *, deal_id: str, tenant_id: str) -> None:
        if self.deal_id != deal_id:
            raise DealAuditScopeError(
                "Audit entry belongs to a different deal."
            )
        if self.tenant_id != tenant_id:
            raise DealAuditScopeError(
                "Audit entry belongs to a different tenant."
            )

    def semantic_key(self) -> tuple[Any, ...]:
        return (
            self.audit_id,
            self.deal_id,
            self.tenant_id,
            self.action,
            self.actor_id,
            dict(self.details),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "audit_id": self.audit_id,
            "deal_id": self.deal_id,
            "tenant_id": self.tenant_id,
            "action": self.action,
            "actor_id": self.actor_id,
            "created_at": self.created_at,
            "details": dict(self.details),
            "version": self.version,
            "source_of_truth": self.source_of_truth,
        }


__all__ = [
    "DealAuditConflictError",
    "DealAuditEntry",
    "DealAuditScopeError",
    "DealEvidenceAuditError",
    "DealEvidenceConflictError",
    "DealEvidenceReference",
    "DealEvidenceScopeError",
]
