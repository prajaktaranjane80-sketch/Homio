"""
CORE-003 T03 — Lead Source & Attribution

Owns:
- source attribution
- attribution evidence references
- deterministic attribution identity
- tenant-safe attribution

Does NOT own:
- lead lifecycle
- ownership assignment
- ownership transfer
- fraud decision
- evidence storage
- event transport
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from uuid import UUID


class LeadAttributionError(Exception):
    """Base attribution error."""


class AttributionValidationError(LeadAttributionError):
    """Invalid attribution data."""


def _validate_uuid(value: UUID, field_name: str) -> UUID:
    if not isinstance(value, UUID):
        raise AttributionValidationError(
            f"{field_name} must be UUID"
        )
    return value


def _text(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise AttributionValidationError(
            f"{field_name} must be non-empty text"
        )

    return value.strip()


def _time(value: datetime, field_name: str) -> datetime:
    if not isinstance(value, datetime):
        raise AttributionValidationError(
            f"{field_name} must be datetime"
        )

    if value.tzinfo is None or value.utcoffset() is None:
        raise AttributionValidationError(
            f"{field_name} must be timezone-aware"
        )

    return value.astimezone(timezone.utc)


@dataclass(frozen=True, slots=True)
class LeadAttribution:
    lead_id: UUID
    tenant_id: UUID
    source_type: str
    source_reference: str
    attributed_at: datetime
    evidence_reference: str | None = None
    campaign_reference: str | None = None
    channel: str | None = None

    def __post_init__(self) -> None:
        _validate_uuid(self.lead_id, "lead_id")
        _validate_uuid(self.tenant_id, "tenant_id")

        object.__setattr__(
            self,
            "source_type",
            _text(self.source_type, "source_type"),
        )

        object.__setattr__(
            self,
            "source_reference",
            _text(
                self.source_reference,
                "source_reference",
            ),
        )

        object.__setattr__(
            self,
            "attributed_at",
            _time(
                self.attributed_at,
                "attributed_at",
            ),
        )

        if self.evidence_reference is not None:
            object.__setattr__(
                self,
                "evidence_reference",
                _text(
                    self.evidence_reference,
                    "evidence_reference",
                ),
            )

        if self.campaign_reference is not None:
            object.__setattr__(
                self,
                "campaign_reference",
                _text(
                    self.campaign_reference,
                    "campaign_reference",
                ),
            )

        if self.channel is not None:
            object.__setattr__(
                self,
                "channel",
                _text(self.channel, "channel"),
            )

    @property
    def attribution_key(self) -> tuple[UUID, UUID, str, str]:
        return (
            self.tenant_id,
            self.lead_id,
            self.source_type,
            self.source_reference,
        )

    @property
    def fingerprint(self) -> str:
        payload = {
            "tenant_id": str(self.tenant_id),
            "lead_id": str(self.lead_id),
            "source_type": self.source_type,
            "source_reference": self.source_reference,
            "attributed_at": self.attributed_at.isoformat(),
            "evidence_reference": self.evidence_reference,
            "campaign_reference": self.campaign_reference,
            "channel": self.channel,
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
        _validate_uuid(tenant_id, "tenant_id")

        if tenant_id != self.tenant_id:
            raise AttributionValidationError(
                "Attribution tenant boundary violation"
            )

    def to_dict(self) -> dict[str, object]:
        return {
            "lead_id": str(self.lead_id),
            "tenant_id": str(self.tenant_id),
            "source_type": self.source_type,
            "source_reference": self.source_reference,
            "attributed_at": self.attributed_at.isoformat(),
            "evidence_reference": self.evidence_reference,
            "campaign_reference": self.campaign_reference,
            "channel": self.channel,
            "fingerprint": self.fingerprint,
        }
