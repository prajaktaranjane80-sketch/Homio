"""
CORE-003 T01 — Lead Domain

Owns:
- Lead identity
- Lead lifecycle
- Lead priority
- Lead source reference
- Tenant-scoped lead identity
- Immutable lead state transitions

Does NOT own:
- Ownership assignment
- Ownership transfer
- Communication evidence
- Fraud decisions
- Trust scoring
- Authorization policy
- Event transport
- Control Center state
- ACRL state
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from enum import Enum
import hashlib
import json
from types import MappingProxyType
from typing import Any, Mapping
from uuid import UUID, uuid4


class LeadDomainError(Exception):
    """Base CORE-003 lead-domain error."""


class LeadValidationError(LeadDomainError):
    """Raised when lead data violates the domain contract."""


class LeadLifecycleError(LeadDomainError):
    """Raised when an invalid lifecycle transition is attempted."""


class LeadTenantViolation(LeadDomainError):
    """Raised when a tenant boundary is violated."""


class LeadStatus(str, Enum):
    NEW = "NEW"
    QUALIFYING = "QUALIFYING"
    QUALIFIED = "QUALIFIED"
    NURTURING = "NURTURING"
    CONVERTED = "CONVERTED"
    LOST = "LOST"
    ARCHIVED = "ARCHIVED"


class LeadPriority(str, Enum):
    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    URGENT = "URGENT"


class LeadSourceType(str, Enum):
    DIRECT = "DIRECT"
    WEBSITE = "WEBSITE"
    PORTAL = "PORTAL"
    REFERRAL = "REFERRAL"
    BUILDER = "BUILDER"
    BROKER = "BROKER"
    PARTNER = "PARTNER"
    CAMPAIGN = "CAMPAIGN"
    IMPORT = "IMPORT"
    API = "API"
    OTHER = "OTHER"


LEAD_STATUS_TRANSITIONS: Mapping[LeadStatus, frozenset[LeadStatus]] = {
    LeadStatus.NEW: frozenset(
        {
            LeadStatus.QUALIFYING,
            LeadStatus.LOST,
            LeadStatus.ARCHIVED,
        }
    ),
    LeadStatus.QUALIFYING: frozenset(
        {
            LeadStatus.QUALIFIED,
            LeadStatus.NURTURING,
            LeadStatus.LOST,
        }
    ),
    LeadStatus.QUALIFIED: frozenset(
        {
            LeadStatus.NURTURING,
            LeadStatus.CONVERTED,
            LeadStatus.LOST,
        }
    ),
    LeadStatus.NURTURING: frozenset(
        {
            LeadStatus.QUALIFYING,
            LeadStatus.QUALIFIED,
            LeadStatus.CONVERTED,
            LeadStatus.LOST,
        }
    ),
    LeadStatus.CONVERTED: frozenset(),
    LeadStatus.LOST: frozenset(
        {
            LeadStatus.NURTURING,
            LeadStatus.ARCHIVED,
        }
    ),
    LeadStatus.ARCHIVED: frozenset(),
}


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _validate_uuid(value: UUID, field_name: str) -> UUID:
    if not isinstance(value, UUID):
        raise LeadValidationError(f"{field_name} must be a UUID")
    return value


def _required_text(value: str, field_name: str) -> str:
    if not isinstance(value, str):
        raise LeadValidationError(f"{field_name} must be a string")

    value = value.strip()

    if not value:
        raise LeadValidationError(f"{field_name} cannot be empty")

    return value


def _validate_aware_datetime(value: datetime, field_name: str) -> datetime:
    if not isinstance(value, datetime):
        raise LeadValidationError(f"{field_name} must be datetime")

    if value.tzinfo is None or value.utcoffset() is None:
        raise LeadValidationError(
            f"{field_name} must be timezone-aware"
        )

    return value.astimezone(timezone.utc)


def _canonicalize(value: Any) -> Any:
    if isinstance(value, UUID):
        return str(value)

    if isinstance(value, datetime):
        return _validate_aware_datetime(value, "datetime").isoformat()

    if isinstance(value, Enum):
        return value.value

    if isinstance(value, Mapping):
        return {
            str(key): _canonicalize(value[key])
            for key in sorted(value, key=lambda item: str(item))
        }

    if isinstance(value, (list, tuple)):
        return [_canonicalize(item) for item in value]

    if isinstance(value, (str, int, float, bool)) or value is None:
        return value

    raise LeadValidationError(
        f"Unsupported value type: {type(value).__name__}"
    )


def _canonical_json(value: Any) -> str:
    return json.dumps(
        _canonicalize(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


@dataclass(frozen=True, slots=True)
class LeadSource:
    source_type: LeadSourceType
    source_id: str | None = None
    campaign_id: str | None = None
    channel: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.source_type, LeadSourceType):
            raise LeadValidationError(
                "source_type must be LeadSourceType"
            )

        if self.source_id is not None:
            _required_text(self.source_id, "source_id")

        if self.campaign_id is not None:
            _required_text(self.campaign_id, "campaign_id")

        if self.channel is not None:
            _required_text(self.channel, "channel")

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_type": self.source_type.value,
            "source_id": self.source_id,
            "campaign_id": self.campaign_id,
            "channel": self.channel,
        }


@dataclass(frozen=True, slots=True)
class Lead:
    lead_id: UUID
    tenant_id: UUID
    customer_id: UUID
    status: LeadStatus
    priority: LeadPriority
    source: LeadSource
    metadata: Mapping[str, Any] = field(
        default_factory=lambda: MappingProxyType({})
    )
    revision: int = 0
    created_at: datetime = field(default_factory=_utc_now)
    updated_at: datetime = field(default_factory=_utc_now)

    def __post_init__(self) -> None:
        _validate_uuid(self.lead_id, "lead_id")
        _validate_uuid(self.tenant_id, "tenant_id")
        _validate_uuid(self.customer_id, "customer_id")

        if not isinstance(self.status, LeadStatus):
            raise LeadValidationError("status must be LeadStatus")

        if not isinstance(self.priority, LeadPriority):
            raise LeadValidationError("priority must be LeadPriority")

        if not isinstance(self.source, LeadSource):
            raise LeadValidationError("source must be LeadSource")

        if not isinstance(self.revision, int) or self.revision < 0:
            raise LeadValidationError(
                "revision must be a non-negative integer"
            )

        created = _validate_aware_datetime(
            self.created_at,
            "created_at",
        )
        updated = _validate_aware_datetime(
            self.updated_at,
            "updated_at",
        )

        if updated < created:
            raise LeadValidationError(
                "updated_at cannot be earlier than created_at"
            )

        if not isinstance(self.metadata, Mapping):
            raise LeadValidationError("metadata must be a mapping")

        normalized_metadata = MappingProxyType(
            {
                str(key): _canonicalize(value)
                for key, value in self.metadata.items()
            }
        )

        object.__setattr__(self, "metadata", normalized_metadata)
        object.__setattr__(self, "created_at", created)
        object.__setattr__(self, "updated_at", updated)

    @classmethod
    def create(
        cls,
        *,
        tenant_id: UUID,
        customer_id: UUID,
        source: LeadSource,
        priority: LeadPriority = LeadPriority.NORMAL,
        metadata: Mapping[str, Any] | None = None,
        lead_id: UUID | None = None,
        created_at: datetime | None = None,
    ) -> "Lead":
        timestamp = _utc_now() if created_at is None else created_at

        return cls(
            lead_id=lead_id or uuid4(),
            tenant_id=tenant_id,
            customer_id=customer_id,
            status=LeadStatus.NEW,
            priority=priority,
            source=source,
            metadata=MappingProxyType(dict(metadata or {})),
            revision=0,
            created_at=timestamp,
            updated_at=timestamp,
        )

    def transition(
        self,
        target_status: LeadStatus,
        *,
        changed_at: datetime | None = None,
    ) -> "Lead":
        if not isinstance(target_status, LeadStatus):
            raise LeadLifecycleError(
                "target_status must be LeadStatus"
            )

        if target_status == self.status:
            raise LeadLifecycleError(
                f"Lead is already in status {self.status.value}"
            )

        allowed = LEAD_STATUS_TRANSITIONS[self.status]

        if target_status not in allowed:
            raise LeadLifecycleError(
                f"Invalid lead lifecycle transition: "
                f"{self.status.value} -> {target_status.value}"
            )

        timestamp = (
            _utc_now()
            if changed_at is None
            else _validate_aware_datetime(changed_at, "changed_at")
        )

        return replace(
            self,
            status=target_status,
            revision=self.revision + 1,
            updated_at=timestamp,
        )

    def with_priority(
        self,
        priority: LeadPriority,
        *,
        changed_at: datetime | None = None,
    ) -> "Lead":
        if not isinstance(priority, LeadPriority):
            raise LeadValidationError("priority must be LeadPriority")

        timestamp = (
            _utc_now()
            if changed_at is None
            else _validate_aware_datetime(changed_at, "changed_at")
        )

        return replace(
            self,
            priority=priority,
            revision=self.revision + 1,
            updated_at=timestamp,
        )

    def with_metadata(
        self,
        metadata: Mapping[str, Any],
        *,
        changed_at: datetime | None = None,
    ) -> "Lead":
        if not isinstance(metadata, Mapping):
            raise LeadValidationError("metadata must be a mapping")

        timestamp = (
            _utc_now()
            if changed_at is None
            else _validate_aware_datetime(changed_at, "changed_at")
        )

        return replace(
            self,
            metadata=MappingProxyType(dict(metadata)),
            revision=self.revision + 1,
            updated_at=timestamp,
        )

    def ensure_tenant(self, tenant_id: UUID) -> None:
        _validate_uuid(tenant_id, "tenant_id")

        if self.tenant_id != tenant_id:
            raise LeadTenantViolation(
                f"Lead {self.lead_id} does not belong to tenant "
                f"{tenant_id}"
            )

    @property
    def identity_key(self) -> tuple[UUID, UUID]:
        return self.tenant_id, self.lead_id

    @property
    def immutable_fingerprint(self) -> str:
        payload = {
            "lead_id": self.lead_id,
            "tenant_id": self.tenant_id,
            "customer_id": self.customer_id,
            "created_at": self.created_at,
        }

        return hashlib.sha256(
            _canonical_json(payload).encode("utf-8")
        ).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        return {
            "lead_id": str(self.lead_id),
            "tenant_id": str(self.tenant_id),
            "customer_id": str(self.customer_id),
            "status": self.status.value,
            "priority": self.priority.value,
            "source": self.source.to_dict(),
            "metadata": dict(self.metadata),
            "revision": self.revision,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "immutable_fingerprint": self.immutable_fingerprint,
        }
