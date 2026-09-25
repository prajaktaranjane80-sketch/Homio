"""Authoritative REOS inventory evidence capability for CORE-004-T06.

T06 owns immutable evidence references associated with an inventory version.

This module deliberately does not store files, upload content, or implement
external storage. It defines the domain-level evidence contract only.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Mapping
from uuid import uuid4


class InventoryEvidenceError(ValueError):
    """Base error for inventory evidence failures."""


class InventoryEvidenceScopeError(InventoryEvidenceError):
    """Raised when evidence is used outside its canonical scope."""


class InventoryEvidenceType(str, Enum):
    OWNERSHIP_DOCUMENT = "OWNERSHIP_DOCUMENT"
    APPROVAL_DOCUMENT = "APPROVAL_DOCUMENT"
    IDENTITY_DOCUMENT = "IDENTITY_DOCUMENT"
    PROPERTY_DOCUMENT = "PROPERTY_DOCUMENT"
    PHOTOGRAPH = "PHOTOGRAPH"
    INSPECTION_REPORT = "INSPECTION_REPORT"
    LEGAL_DOCUMENT = "LEGAL_DOCUMENT"
    OTHER = "OTHER"


class InventoryEvidenceStatus(str, Enum):
    REGISTERED = "REGISTERED"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"
    REVOKED = "REVOKED"


@dataclass(frozen=True)
class InventoryEvidenceEvent:
    """Persistence-neutral evidence event."""

    event_id: str
    event_type: str
    evidence_id: str
    inventory_id: str
    tenant_id: str
    project_id: str
    inventory_version: int
    status: InventoryEvidenceStatus
    occurred_at: str
    payload: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "evidence_id": self.evidence_id,
            "inventory_id": self.inventory_id,
            "tenant_id": self.tenant_id,
            "project_id": self.project_id,
            "inventory_version": self.inventory_version,
            "status": self.status.value,
            "occurred_at": self.occurred_at,
            "payload": dict(self.payload),
        }


@dataclass(frozen=True)
class InventoryEvidence:
    """Immutable evidence reference linked to one inventory version."""

    evidence_id: str
    inventory_id: str
    tenant_id: str
    project_id: str
    inventory_version: int
    evidence_type: InventoryEvidenceType
    reference: str
    status: InventoryEvidenceStatus
    submitted_by: str
    created_at: str
    updated_at: str
    version: int = 1
    metadata: Mapping[str, Any] = field(default_factory=dict)
    source_of_truth: str = "inventory_evidence"

    def __post_init__(self) -> None:
        if not self.evidence_id.strip():
            raise InventoryEvidenceError("evidence_id is required.")

        if not self.inventory_id.strip():
            raise InventoryEvidenceError("inventory_id is required.")

        if not self.tenant_id.strip():
            raise InventoryEvidenceError("tenant_id is required.")

        if not self.project_id.strip():
            raise InventoryEvidenceError("project_id is required.")

        if self.inventory_version < 1:
            raise InventoryEvidenceError(
                "inventory_version must be >= 1."
            )

        if not self.reference.strip():
            raise InventoryEvidenceError("evidence reference is required.")

        if not self.submitted_by.strip():
            raise InventoryEvidenceError("submitted_by is required.")

        if self.version < 1:
            raise InventoryEvidenceError("version must be >= 1.")

        if self.source_of_truth != "inventory_evidence":
            raise InventoryEvidenceError(
                "Evidence must remain authoritative within its own capability."
            )

        object.__setattr__(
            self,
            "evidence_type",
            InventoryEvidenceType(self.evidence_type),
        )
        object.__setattr__(
            self,
            "status",
            InventoryEvidenceStatus(self.status),
        )

    @classmethod
    def register(
        cls,
        *,
        inventory_id: str,
        tenant_id: str,
        project_id: str,
        inventory_version: int,
        evidence_type: InventoryEvidenceType,
        reference: str,
        submitted_by: str,
        metadata: Mapping[str, Any] | None = None,
        evidence_id: str | None = None,
        at: str | None = None,
    ) -> "InventoryEvidence":
        timestamp = at or datetime.now(timezone.utc).isoformat(
            timespec="seconds"
        )

        return cls(
            evidence_id=evidence_id or str(uuid4()),
            inventory_id=inventory_id,
            tenant_id=tenant_id,
            project_id=project_id,
            inventory_version=inventory_version,
            evidence_type=InventoryEvidenceType(evidence_type),
            reference=reference,
            status=InventoryEvidenceStatus.REGISTERED,
            submitted_by=submitted_by,
            created_at=timestamp,
            updated_at=timestamp,
            metadata=dict(metadata or {}),
        )

    def assert_scope(
        self,
        *,
        tenant_id: str,
        project_id: str,
        inventory_id: str,
    ) -> None:
        if tenant_id != self.tenant_id:
            raise InventoryEvidenceScopeError(
                "Evidence belongs to a different tenant."
            )

        if project_id != self.project_id:
            raise InventoryEvidenceScopeError(
                "Evidence belongs to a different project."
            )

        if inventory_id != self.inventory_id:
            raise InventoryEvidenceScopeError(
                "Evidence belongs to a different inventory."
            )

    def with_status(
        self,
        status: InventoryEvidenceStatus,
        *,
        tenant_id: str,
        project_id: str,
        inventory_id: str,
        at: str | None = None,
    ) -> tuple["InventoryEvidence", InventoryEvidenceEvent]:
        self.assert_scope(
            tenant_id=tenant_id,
            project_id=project_id,
            inventory_id=inventory_id,
        )

        target = InventoryEvidenceStatus(status)

        timestamp = at or datetime.now(timezone.utc).isoformat(
            timespec="seconds"
        )

        updated = InventoryEvidence(
            evidence_id=self.evidence_id,
            inventory_id=self.inventory_id,
            tenant_id=self.tenant_id,
            project_id=self.project_id,
            inventory_version=self.inventory_version,
            evidence_type=self.evidence_type,
            reference=self.reference,
            status=target,
            submitted_by=self.submitted_by,
            created_at=self.created_at,
            updated_at=timestamp,
            version=self.version + 1,
            metadata=dict(self.metadata),
        )

        event = InventoryEvidenceEvent(
            event_id=str(uuid4()),
            event_type="INVENTORY_EVIDENCE_STATUS_CHANGED",
            evidence_id=self.evidence_id,
            inventory_id=self.inventory_id,
            tenant_id=self.tenant_id,
            project_id=self.project_id,
            inventory_version=self.inventory_version,
            status=target,
            occurred_at=timestamp,
            payload={
                "from": self.status.value,
                "to": target.value,
                "evidence_version": updated.version,
            },
        )

        return updated, event

    def to_dict(self) -> dict[str, Any]:
        return {
            "evidence_id": self.evidence_id,
            "inventory_id": self.inventory_id,
            "tenant_id": self.tenant_id,
            "project_id": self.project_id,
            "inventory_version": self.inventory_version,
            "evidence_type": self.evidence_type.value,
            "reference": self.reference,
            "status": self.status.value,
            "submitted_by": self.submitted_by,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "version": self.version,
            "metadata": dict(self.metadata),
            "source_of_truth": self.source_of_truth,
        }


__all__ = [
    "InventoryEvidence",
    "InventoryEvidenceError",
    "InventoryEvidenceEvent",
    "InventoryEvidenceScopeError",
    "InventoryEvidenceStatus",
    "InventoryEvidenceType",
]