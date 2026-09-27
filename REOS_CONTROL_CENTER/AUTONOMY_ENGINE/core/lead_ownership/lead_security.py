"""
CORE-003 T09 — Security & Tenant Boundary

Purpose:
- Enforce tenant isolation at the CORE-003 boundary.
- Consume externally established authorization capabilities.
- Fail closed when tenant/capability context is absent or inconsistent.

IMPORTANT:
This is NOT an authorization engine.
CORE-001 remains the authority for identity/roles/permissions.

CORE-003 only verifies the security context presented to it.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from uuid import UUID

from .lead import Lead
from .lead_ownership import LeadOwnership


class LeadSecurityError(Exception):
    """Base CORE-003 security error."""


class LeadTenantBoundaryViolation(
    LeadSecurityError
):
    """Cross-tenant access or mutation attempt."""


class LeadCapabilityViolation(
    LeadSecurityError
):
    """Required externally-granted capability is missing."""


class LeadSecurityContextError(
    LeadSecurityError
):
    """Invalid or incomplete security context."""


class LeadCapability(str, Enum):
    READ_LEAD = "READ_LEAD"
    CREATE_LEAD = "CREATE_LEAD"
    TRANSITION_LEAD = "TRANSITION_LEAD"
    UPDATE_LEAD = "UPDATE_LEAD"
    ASSIGN_LEAD = "ASSIGN_LEAD"
    TRANSFER_LEAD = "TRANSFER_LEAD"
    ATTACH_COMMUNICATION_EVIDENCE = (
        "ATTACH_COMMUNICATION_EVIDENCE"
    )
    CREATE_FRAUD_HANDOFF = "CREATE_FRAUD_HANDOFF"


def _uuid(value: UUID, field_name: str) -> UUID:
    if not isinstance(value, UUID):
        raise LeadSecurityContextError(
            f"{field_name} must be UUID"
        )
    return value


def _text(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise LeadSecurityContextError(
            f"{field_name} must be non-empty text"
        )
    return value.strip()


def _time(value: datetime, field_name: str) -> datetime:
    if not isinstance(value, datetime):
        raise LeadSecurityContextError(
            f"{field_name} must be datetime"
        )

    if value.tzinfo is None or value.utcoffset() is None:
        raise LeadSecurityContextError(
            f"{field_name} must be timezone-aware"
        )

    return value.astimezone(timezone.utc)


@dataclass(frozen=True, slots=True)
class LeadSecurityContext:
    tenant_id: UUID
    actor_id: UUID
    capabilities: frozenset[LeadCapability]
    authorization_reference: str
    issued_at: datetime
    expires_at: datetime | None = None
    request_id: UUID | None = None

    def __post_init__(self) -> None:
        _uuid(self.tenant_id, "tenant_id")
        _uuid(self.actor_id, "actor_id")

        if not isinstance(
            self.capabilities,
            frozenset,
        ):
            raise LeadSecurityContextError(
                "capabilities must be frozenset"
            )

        for capability in self.capabilities:
            if not isinstance(
                capability,
                LeadCapability,
            ):
                raise LeadSecurityContextError(
                    "capabilities contains invalid value"
                )

        object.__setattr__(
            self,
            "authorization_reference",
            _text(
                self.authorization_reference,
                "authorization_reference",
            ),
        )

        object.__setattr__(
            self,
            "issued_at",
            _time(self.issued_at, "issued_at"),
        )

        if self.expires_at is not None:
            object.__setattr__(
                self,
                "expires_at",
                _time(
                    self.expires_at,
                    "expires_at",
                ),
            )

            if self.expires_at <= self.issued_at:
                raise LeadSecurityContextError(
                    "expires_at must be later than issued_at"
                )

        if self.request_id is not None:
            _uuid(self.request_id, "request_id")

    def ensure_tenant(self, tenant_id: UUID) -> None:
        _uuid(tenant_id, "tenant_id")

        if self.tenant_id != tenant_id:
            raise LeadTenantBoundaryViolation(
                "Security context tenant mismatch"
            )

    def ensure_lead(self, lead: Lead) -> None:
        if not isinstance(lead, Lead):
            raise LeadSecurityContextError(
                "lead must be Lead"
            )

        self.ensure_tenant(lead.tenant_id)

    def ensure_ownership(
        self,
        ownership: LeadOwnership,
    ) -> None:
        if not isinstance(
            ownership,
            LeadOwnership,
        ):
            raise LeadSecurityContextError(
                "ownership must be LeadOwnership"
            )

        self.ensure_tenant(ownership.tenant_id)

    def require(
        self,
        capability: LeadCapability,
    ) -> None:
        if not isinstance(
            capability,
            LeadCapability,
        ):
            raise LeadCapabilityViolation(
                "capability must be LeadCapability"
            )

        if capability not in self.capabilities:
            raise LeadCapabilityViolation(
                f"Capability not granted: {capability.value}"
            )

    def assert_active(
        self,
        *,
        now: datetime | None = None,
    ) -> None:
        timestamp = (
            datetime.now(timezone.utc)
            if now is None
            else _time(now, "now")
        )

        if timestamp < self.issued_at:
            raise LeadSecurityContextError(
                "Security context is not active yet"
            )

        if (
            self.expires_at is not None
            and timestamp >= self.expires_at
        ):
            raise LeadSecurityContextError(
                "Security context has expired"
            )
