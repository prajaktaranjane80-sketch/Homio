"""
CORE-003 T04 — Lead Ownership

First-class tenant-scoped lead ownership binding.

Owns:
- current ownership binding
- ownership role
- assignment revision
- assignment timestamps
- ownership integrity

Does NOT own:
- ownership history
- transfer workflow
- fraud decisions
- commission
- deal ownership
- authorization policy engine
- evidence storage
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
import hashlib
import json
from uuid import UUID


class LeadOwnershipError(Exception):
    """Base lead ownership error."""


class OwnershipValidationError(LeadOwnershipError):
    """Invalid ownership data."""


class OwnershipTenantViolation(LeadOwnershipError):
    """Tenant boundary violation."""


class OwnershipConflictError(LeadOwnershipError):
    """Ownership revision conflict."""


class LeadOwnerRole(str, Enum):
    BROKERAGE = "BROKERAGE"
    BROKER = "BROKER"
    AGENT = "AGENT"
    PARTNER = "PARTNER"
    BUILDER = "BUILDER"
    PLATFORM = "PLATFORM"


def _uuid(value: UUID, field_name: str) -> UUID:
    if not isinstance(value, UUID):
        raise OwnershipValidationError(
            f"{field_name} must be UUID"
        )

    return value


def _time(value: datetime, field_name: str) -> datetime:
    if not isinstance(value, datetime):
        raise OwnershipValidationError(
            f"{field_name} must be datetime"
        )

    if value.tzinfo is None or value.utcoffset() is None:
        raise OwnershipValidationError(
            f"{field_name} must be timezone-aware"
        )

    return value.astimezone(timezone.utc)


@dataclass(frozen=True, slots=True)
class LeadOwnership:
    lead_id: UUID
    tenant_id: UUID
    owner_id: UUID
    owner_role: LeadOwnerRole
    assigned_at: datetime
    revision: int = 0
    assignment_reference: str | None = None

    def __post_init__(self) -> None:
        _uuid(self.lead_id, "lead_id")
        _uuid(self.tenant_id, "tenant_id")
        _uuid(self.owner_id, "owner_id")

        if not isinstance(self.owner_role, LeadOwnerRole):
            raise OwnershipValidationError(
                "owner_role must be LeadOwnerRole"
            )

        object.__setattr__(
            self,
            "assigned_at",
            _time(self.assigned_at, "assigned_at"),
        )

        if not isinstance(self.revision, int) or self.revision < 0:
            raise OwnershipValidationError(
                "revision must be non-negative integer"
            )

        if self.assignment_reference is not None:
            if not isinstance(
                self.assignment_reference,
                str,
            ) or not self.assignment_reference.strip():
                raise OwnershipValidationError(
                    "assignment_reference must be non-empty"
                )

            object.__setattr__(
                self,
                "assignment_reference",
                self.assignment_reference.strip(),
            )

    @classmethod
    def create(
        cls,
        *,
        lead_id: UUID,
        tenant_id: UUID,
        owner_id: UUID,
        owner_role: LeadOwnerRole,
        assigned_at: datetime | None = None,
        assignment_reference: str | None = None,
    ) -> "LeadOwnership":
        timestamp = (
            datetime.now(timezone.utc)
            if assigned_at is None
            else assigned_at
        )

        return cls(
            lead_id=lead_id,
            tenant_id=tenant_id,
            owner_id=owner_id,
            owner_role=owner_role,
            assigned_at=timestamp,
            revision=0,
            assignment_reference=assignment_reference,
        )

    def ensure_tenant(self, tenant_id: UUID) -> None:
        _uuid(tenant_id, "tenant_id")

        if self.tenant_id != tenant_id:
            raise OwnershipTenantViolation(
                "Lead ownership belongs to another tenant"
            )

    def ensure_lead(self, lead_id: UUID) -> None:
        _uuid(lead_id, "lead_id")

        if self.lead_id != lead_id:
            raise OwnershipValidationError(
                "Ownership does not belong to supplied lead"
            )

    def rebind(
        self,
        *,
        owner_id: UUID,
        owner_role: LeadOwnerRole,
        expected_revision: int,
        assigned_at: datetime | None = None,
        assignment_reference: str | None = None,
    ) -> "LeadOwnership":
        _uuid(owner_id, "owner_id")

        if not isinstance(owner_role, LeadOwnerRole):
            raise OwnershipValidationError(
                "owner_role must be LeadOwnerRole"
            )

        if expected_revision != self.revision:
            raise OwnershipConflictError(
                f"Ownership revision conflict: expected "
                f"{expected_revision}, actual {self.revision}"
            )

        if owner_id == self.owner_id:
            raise OwnershipValidationError(
                "New owner must differ from current owner"
            )

        timestamp = (
            datetime.now(timezone.utc)
            if assigned_at is None
            else _time(assigned_at, "assigned_at")
        )

        return LeadOwnership(
            lead_id=self.lead_id,
            tenant_id=self.tenant_id,
            owner_id=owner_id,
            owner_role=owner_role,
            assigned_at=timestamp,
            revision=self.revision + 1,
            assignment_reference=assignment_reference,
        )

    @property
    def binding_key(self) -> tuple[UUID, UUID]:
        return self.tenant_id, self.lead_id

    @property
    def fingerprint(self) -> str:
        payload = {
            "tenant_id": str(self.tenant_id),
            "lead_id": str(self.lead_id),
            "owner_id": str(self.owner_id),
            "owner_role": self.owner_role.value,
            "assigned_at": self.assigned_at.isoformat(),
            "revision": self.revision,
            "assignment_reference": self.assignment_reference,
        }

        canonical = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
        )

        return hashlib.sha256(
            canonical.encode("utf-8")
        ).hexdigest()

    def to_dict(self) -> dict[str, object]:
        return {
            "lead_id": str(self.lead_id),
            "tenant_id": str(self.tenant_id),
            "owner_id": str(self.owner_id),
            "owner_role": self.owner_role.value,
            "assigned_at": self.assigned_at.isoformat(),
            "revision": self.revision,
            "assignment_reference": self.assignment_reference,
            "fingerprint": self.fingerprint,
        }
