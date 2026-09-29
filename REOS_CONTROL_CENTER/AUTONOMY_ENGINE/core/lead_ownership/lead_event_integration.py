"""
CORE-003 T11 — CORE-002 Domain Event Integration

This module defines the CORE-003 -> CORE-002 domain-event boundary.

CORE-003 owns:
- Lead domain truth
- Ownership truth
- Attribution
- Evidence hooks
- Fraud handoff signals

CORE-002 owns:
- Event domain contract
- Event envelope semantics
- Event validation
- Event platform behavior

This module DOES NOT:
- publish events
- persist events
- implement an event bus
- implement Kafka
- implement an outbox
- duplicate CORE-002
- mutate Control Center state
- mutate ACRL state
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
import hashlib
import json
from types import MappingProxyType
from typing import Any, Mapping
from uuid import UUID, uuid4


class LeadEventIntegrationError(Exception):
    """Base CORE-003 event integration error."""


class LeadEventValidationError(
    LeadEventIntegrationError
):
    """Invalid CORE-003 domain-event contract."""


class LeadEventConflictError(
    LeadEventIntegrationError
):
    """Conflicting domain-event identity."""


class LeadDomainEventType(str, Enum):
    LEAD_CREATED = "LEAD_CREATED"
    LEAD_STATUS_CHANGED = "LEAD_STATUS_CHANGED"
    LEAD_OWNER_ASSIGNED = "LEAD_OWNER_ASSIGNED"
    LEAD_OWNER_TRANSFERRED = "LEAD_OWNER_TRANSFERRED"
    LEAD_COMMUNICATION_EVIDENCE_ATTACHED = (
        "LEAD_COMMUNICATION_EVIDENCE_ATTACHED"
    )
    LEAD_FRAUD_HANDOFF_CREATED = (
        "LEAD_FRAUD_HANDOFF_CREATED"
    )


def _uuid(value: UUID, field_name: str) -> UUID:
    if not isinstance(value, UUID):
        raise LeadEventValidationError(
            f"{field_name} must be UUID"
        )
    return value


def _text(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise LeadEventValidationError(
            f"{field_name} must be non-empty text"
        )
    return value.strip()


def _time(value: datetime, field_name: str) -> datetime:
    if not isinstance(value, datetime):
        raise LeadEventValidationError(
            f"{field_name} must be datetime"
        )

    if value.tzinfo is None or value.utcoffset() is None:
        raise LeadEventValidationError(
            f"{field_name} must be timezone-aware"
        )

    return value.astimezone(timezone.utc)


def _canonicalize(value: Any) -> Any:
    if isinstance(value, UUID):
        return str(value)

    if isinstance(value, datetime):
        return _time(value, "datetime").isoformat()

    if isinstance(value, Enum):
        return value.value

    if isinstance(value, Mapping):
        return {
            str(key): _canonicalize(value[key])
            for key in sorted(
                value,
                key=lambda item: str(item),
            )
        }

    if isinstance(value, (tuple, list)):
        return [_canonicalize(item) for item in value]

    if isinstance(value, (str, int, float, bool)) or value is None:
        return value

    raise LeadEventValidationError(
        f"Unsupported event payload type: "
        f"{type(value).__name__}"
    )


@dataclass(frozen=True, slots=True)
class LeadDomainEvent:
    """
    Immutable CORE-003 event specification.

    This is an integration contract, not an event transport.
    """

    event_id: UUID
    tenant_id: UUID
    lead_id: UUID
    event_type: LeadDomainEventType
    schema_version: int
    correlation_id: UUID
    causation_id: UUID | None
    idempotency_key: str
    payload: Mapping[str, Any]
    occurred_at: datetime
    producer: str = "CORE-003"

    def __post_init__(self) -> None:
        _uuid(self.event_id, "event_id")
        _uuid(self.tenant_id, "tenant_id")
        _uuid(self.lead_id, "lead_id")
        _uuid(
            self.correlation_id,
            "correlation_id",
        )

        if self.causation_id is not None:
            _uuid(
                self.causation_id,
                "causation_id",
            )

        if not isinstance(
            self.event_type,
            LeadDomainEventType,
        ):
            raise LeadEventValidationError(
                "event_type must be LeadDomainEventType"
            )

        if (
            not isinstance(
                self.schema_version,
                int,
            )
            or self.schema_version < 1
        ):
            raise LeadEventValidationError(
                "schema_version must be >= 1"
            )

        object.__setattr__(
            self,
            "idempotency_key",
            _text(
                self.idempotency_key,
                "idempotency_key",
            ),
        )

        if not isinstance(self.payload, Mapping):
            raise LeadEventValidationError(
                "payload must be a mapping"
            )

        normalized_payload = MappingProxyType(
            {
                str(key): _canonicalize(value)
                for key, value in self.payload.items()
            }
        )

        object.__setattr__(
            self,
            "payload",
            normalized_payload,
        )

        object.__setattr__(
            self,
            "occurred_at",
            _time(
                self.occurred_at,
                "occurred_at",
            ),
        )

        object.__setattr__(
            self,
            "producer",
            _text(
                self.producer,
                "producer",
            ),
        )

    @classmethod
    def create(
        cls,
        *,
        tenant_id: UUID,
        lead_id: UUID,
        event_type: LeadDomainEventType,
        correlation_id: UUID,
        idempotency_key: str,
        payload: Mapping[str, Any],
        causation_id: UUID | None = None,
        event_id: UUID | None = None,
        occurred_at: datetime | None = None,
        schema_version: int = 1,
        producer: str = "CORE-003",
    ) -> "LeadDomainEvent":
        return cls(
            event_id=event_id or uuid4(),
            tenant_id=tenant_id,
            lead_id=lead_id,
            event_type=event_type,
            schema_version=schema_version,
            correlation_id=correlation_id,
            causation_id=causation_id,
            idempotency_key=idempotency_key,
            payload=payload,
            occurred_at=(
                occurred_at
                or datetime.now(timezone.utc)
            ),
            producer=producer,
        )

    @property
    def identity_key(self) -> tuple[UUID, UUID, str]:
        return (
            self.tenant_id,
            self.lead_id,
            self.idempotency_key,
        )

    @property
    def fingerprint(self) -> str:
        payload = {
            "event_id": str(self.event_id),
            "tenant_id": str(self.tenant_id),
            "lead_id": str(self.lead_id),
            "event_type": self.event_type.value,
            "schema_version": self.schema_version,
            "correlation_id": str(
                self.correlation_id
            ),
            "causation_id": (
                str(self.causation_id)
                if self.causation_id is not None
                else None
            ),
            "idempotency_key": self.idempotency_key,
            "payload": dict(self.payload),
            "occurred_at": self.occurred_at.isoformat(),
            "producer": self.producer,
        }

        canonical = json.dumps(
            _canonicalize(payload),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )

        return hashlib.sha256(
            canonical.encode("utf-8")
        ).hexdigest()

    def ensure_tenant(
        self,
        tenant_id: UUID,
    ) -> None:
        _uuid(tenant_id, "tenant_id")

        if tenant_id != self.tenant_id:
            raise LeadEventValidationError(
                "Event tenant boundary violation"
            )

    def assert_compatible(
        self,
        other: "LeadDomainEvent",
    ) -> None:
        if not isinstance(
            other,
            LeadDomainEvent,
        ):
            raise LeadEventValidationError(
                "other must be LeadDomainEvent"
            )

        if self.identity_key != other.identity_key:
            raise LeadEventConflictError(
                "Domain event identities differ"
            )

        if self.fingerprint != other.fingerprint:
            raise LeadEventConflictError(
                "Same event identity has conflicting payload"
            )

    def to_core002_payload(self) -> dict[str, Any]:
        """
        Canonical representation consumed by the existing
        CORE-002 Event Platform boundary.
        """
        return {
            "event_id": str(self.event_id),
            "event_type": self.event_type.value,
            "schema_version": self.schema_version,
            "tenant_id": str(self.tenant_id),
            "producer": self.producer,
            "correlation_id": str(
                self.correlation_id
            ),
            "causation_id": (
                str(self.causation_id)
                if self.causation_id is not None
                else None
            ),
            "occurred_at": self.occurred_at.isoformat(),
            "idempotency_key": self.idempotency_key,
            "payload": dict(self.payload),
            "fingerprint": self.fingerprint,
        }

    def to_dict(self) -> dict[str, Any]:
        return self.to_core002_payload()
