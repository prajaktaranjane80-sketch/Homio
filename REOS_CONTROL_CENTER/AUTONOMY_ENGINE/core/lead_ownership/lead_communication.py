"""
CORE-003 T06 — Communication Evidence Hooks

Purpose:
- Attach immutable communication-event references to a lead.
- Preserve evidence provenance without storing communication content.
- Provide deterministic identity/fingerprint for evidence linkage.

This is a HOOK contract only.

Does NOT own:
- communication storage
- message body/content
- audit storage
- evidence repository
- event transport
- fraud decisions
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
import hashlib
import json
from uuid import UUID


class CommunicationEvidenceError(Exception):
    """Base communication evidence error."""


class CommunicationEvidenceValidationError(
    CommunicationEvidenceError
):
    """Invalid communication evidence hook."""


class CommunicationEvidenceConflictError(
    CommunicationEvidenceError
):
    """Conflicting communication evidence identity."""


class CommunicationDirection(str, Enum):
    INBOUND = "INBOUND"
    OUTBOUND = "OUTBOUND"
    INTERNAL = "INTERNAL"
    EXTERNAL = "EXTERNAL"


class CommunicationChannel(str, Enum):
    PHONE = "PHONE"
    EMAIL = "EMAIL"
    SMS = "SMS"
    WHATSAPP = "WHATSAPP"
    CHAT = "CHAT"
    MEETING = "MEETING"
    PORTAL = "PORTAL"
    OTHER = "OTHER"


def _uuid(value: UUID, field_name: str) -> UUID:
    if not isinstance(value, UUID):
        raise CommunicationEvidenceValidationError(
            f"{field_name} must be UUID"
        )
    return value


def _text(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise CommunicationEvidenceValidationError(
            f"{field_name} must be non-empty text"
        )
    return value.strip()


def _time(value: datetime, field_name: str) -> datetime:
    if not isinstance(value, datetime):
        raise CommunicationEvidenceValidationError(
            f"{field_name} must be datetime"
        )

    if value.tzinfo is None or value.utcoffset() is None:
        raise CommunicationEvidenceValidationError(
            f"{field_name} must be timezone-aware"
        )

    return value.astimezone(timezone.utc)


def _validate_digest(value: str) -> str:
    value = _text(value, "content_digest")

    if len(value) != 64:
        raise CommunicationEvidenceValidationError(
            "content_digest must be a SHA-256 hexadecimal digest"
        )

    try:
        int(value, 16)
    except ValueError as exc:
        raise CommunicationEvidenceValidationError(
            "content_digest must be hexadecimal"
        ) from exc

    return value.lower()


@dataclass(frozen=True, slots=True)
class LeadCommunicationEvidenceHook:
    lead_id: UUID
    tenant_id: UUID
    communication_id: UUID
    evidence_reference: str
    direction: CommunicationDirection
    channel: CommunicationChannel
    occurred_at: datetime
    actor_id: UUID | None = None
    correlation_id: UUID | None = None
    content_digest: str | None = None

    def __post_init__(self) -> None:
        _uuid(self.lead_id, "lead_id")
        _uuid(self.tenant_id, "tenant_id")
        _uuid(self.communication_id, "communication_id")

        _text(
            self.evidence_reference,
            "evidence_reference",
        )

        if not isinstance(
            self.direction,
            CommunicationDirection,
        ):
            raise CommunicationEvidenceValidationError(
                "direction must be CommunicationDirection"
            )

        if not isinstance(
            self.channel,
            CommunicationChannel,
        ):
            raise CommunicationEvidenceValidationError(
                "channel must be CommunicationChannel"
            )

        object.__setattr__(
            self,
            "occurred_at",
            _time(self.occurred_at, "occurred_at"),
        )

        if self.actor_id is not None:
            _uuid(self.actor_id, "actor_id")

        if self.correlation_id is not None:
            _uuid(self.correlation_id, "correlation_id")

        if self.content_digest is not None:
            object.__setattr__(
                self,
                "content_digest",
                _validate_digest(self.content_digest),
            )

    @property
    def evidence_key(self) -> tuple[UUID, UUID, UUID]:
        return (
            self.tenant_id,
            self.lead_id,
            self.communication_id,
        )

    @property
    def fingerprint(self) -> str:
        payload = {
            "tenant_id": str(self.tenant_id),
            "lead_id": str(self.lead_id),
            "communication_id": str(self.communication_id),
            "evidence_reference": self.evidence_reference,
            "direction": self.direction.value,
            "channel": self.channel.value,
            "occurred_at": self.occurred_at.isoformat(),
            "actor_id": (
                str(self.actor_id)
                if self.actor_id is not None
                else None
            ),
            "correlation_id": (
                str(self.correlation_id)
                if self.correlation_id is not None
                else None
            ),
            "content_digest": self.content_digest,
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
            raise CommunicationEvidenceValidationError(
                "Communication evidence tenant violation"
            )

    def ensure_lead(self, lead_id: UUID) -> None:
        _uuid(lead_id, "lead_id")

        if lead_id != self.lead_id:
            raise CommunicationEvidenceValidationError(
                "Communication evidence does not belong to lead"
            )

    def assert_compatible(
        self,
        other: "LeadCommunicationEvidenceHook",
    ) -> None:
        if not isinstance(
            other,
            LeadCommunicationEvidenceHook,
        ):
            raise CommunicationEvidenceValidationError(
                "other must be LeadCommunicationEvidenceHook"
            )

        if self.evidence_key != other.evidence_key:
            raise CommunicationEvidenceConflictError(
                "Communication evidence identities differ"
            )

        if self.fingerprint != other.fingerprint:
            raise CommunicationEvidenceConflictError(
                "Same communication identity has conflicting evidence"
            )

    def to_dict(self) -> dict[str, object]:
        return {
            "lead_id": str(self.lead_id),
            "tenant_id": str(self.tenant_id),
            "communication_id": str(
                self.communication_id
            ),
            "evidence_reference": self.evidence_reference,
            "direction": self.direction.value,
            "channel": self.channel.value,
            "occurred_at": self.occurred_at.isoformat(),
            "actor_id": (
                str(self.actor_id)
                if self.actor_id is not None
                else None
            ),
            "correlation_id": (
                str(self.correlation_id)
                if self.correlation_id is not None
                else None
            ),
            "content_digest": self.content_digest,
            "fingerprint": self.fingerprint,
        }
