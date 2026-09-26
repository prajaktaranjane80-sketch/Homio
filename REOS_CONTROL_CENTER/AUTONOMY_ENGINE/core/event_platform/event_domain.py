from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
from types import MappingProxyType
from typing import Any, Mapping
from uuid import UUID, uuid4
import json


class EventDomainError(ValueError):
    """Base error for CORE-002 event-domain violations."""


class EventValidationError(EventDomainError):
    """Raised when an event violates the canonical event contract."""


class EventTenantViolation(EventDomainError):
    """Raised when an event crosses a tenant boundary."""


class EventMutationError(EventDomainError):
    """Raised when immutable event state is modified."""


class EventSerializationError(EventDomainError):
    """Raised when canonical event serialization fails."""


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _validate_uuid(value: UUID, field_name: str) -> UUID:
    if not isinstance(value, UUID):
        raise TypeError(f"{field_name} must be UUID")
    return value


def _required_text(
    value: str,
    field_name: str,
    max_length: int = 255,
) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be string")

    normalized = value.strip()

    if not normalized:
        raise ValueError(f"{field_name} cannot be empty")

    if len(normalized) > max_length:
        raise ValueError(
            f"{field_name} exceeds maximum length {max_length}"
        )

    if any(ord(ch) < 32 for ch in normalized):
        raise ValueError(
            f"{field_name} contains control characters"
        )

    return normalized


def _validate_aware_datetime(
    value: datetime,
    field_name: str,
) -> datetime:
    if not isinstance(value, datetime):
        raise TypeError(f"{field_name} must be datetime")

    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(
            f"{field_name} must be timezone-aware"
        )

    return value.astimezone(timezone.utc)


def _canonicalize(value: Any) -> Any:
    if isinstance(value, UUID):
        return str(value)

    if isinstance(value, datetime):
        return _validate_aware_datetime(
            value,
            "datetime",
        ).isoformat()

    if isinstance(value, Mapping):
        return {
            str(key): _canonicalize(value[key])
            for key in sorted(value, key=lambda item: str(item))
        }

    if isinstance(value, (list, tuple)):
        return [_canonicalize(item) for item in value]

    if isinstance(value, (str, int, float, bool)) or value is None:
        return value

    raise TypeError(
        f"unsupported event payload type: {type(value).__name__}"
    )


def _canonical_json(value: Any) -> str:
    try:
        return json.dumps(
            _canonicalize(value),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
    except (TypeError, ValueError) as exc:
        raise EventSerializationError(
            "event cannot be canonically serialized"
        ) from exc


@dataclass(frozen=True, slots=True)
class EventTraceContext:
    """
    Immutable distributed-trace context.

    CORE-002 owns propagation metadata only.
    It does not own tracing infrastructure.
    """

    trace_id: str
    span_id: str
    trace_flags: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "trace_id",
            _required_text(
                self.trace_id,
                "trace_id",
                255,
            ),
        )

        object.__setattr__(
            self,
            "span_id",
            _required_text(
                self.span_id,
                "span_id",
                255,
            ),
        )

        object.__setattr__(
            self,
            "trace_flags",
            _required_text(
                self.trace_flags,
                "trace_flags",
                64,
            )
            if self.trace_flags
            else "",
        )

    def to_dict(self) -> dict[str, str]:
        return {
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "trace_flags": self.trace_flags,
        }


@dataclass(frozen=True, slots=True)
class EventEnvelope:
    """
    Canonical immutable CORE-002 event envelope.

    This is the domain contract.

    Deliberately NOT:
    - a Kafka message
    - a database record
    - an outbox implementation
    - a replay engine
    - an audit engine
    - Control Center state
    """

    event_id: UUID
    event_type: str
    schema_name: str
    schema_version: int
    event_version: int

    tenant_id: UUID
    producer_id: UUID

    correlation_id: UUID
    causation_id: UUID | None

    occurred_at: datetime
    observed_at: datetime

    payload: Mapping[str, Any]

    trace_context: EventTraceContext | None = None

    ordering_key: str | None = None
    sequence: int | None = None

    idempotency_key: str | None = None

    metadata: Mapping[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        _validate_uuid(
            self.event_id,
            "event_id",
        )
        _validate_uuid(
            self.tenant_id,
            "tenant_id",
        )
        _validate_uuid(
            self.producer_id,
            "producer_id",
        )
        _validate_uuid(
            self.correlation_id,
            "correlation_id",
        )

        if self.causation_id is not None:
            _validate_uuid(
                self.causation_id,
                "causation_id",
            )

        object.__setattr__(
            self,
            "event_type",
            _required_text(
                self.event_type,
                "event_type",
                200,
            ),
        )

        object.__setattr__(
            self,
            "schema_name",
            _required_text(
                self.schema_name,
                "schema_name",
                200,
            ),
        )

        if not isinstance(
            self.schema_version,
            int,
        ):
            raise TypeError(
                "schema_version must be int"
            )

        if self.schema_version < 1:
            raise ValueError(
                "schema_version must be >= 1"
            )

        if not isinstance(
            self.event_version,
            int,
        ):
            raise TypeError(
                "event_version must be int"
            )

        if self.event_version < 1:
            raise ValueError(
                "event_version must be >= 1"
            )

        occurred_at = _validate_aware_datetime(
            self.occurred_at,
            "occurred_at",
        )

        observed_at = _validate_aware_datetime(
            self.observed_at,
            "observed_at",
        )

        if observed_at < occurred_at:
            raise ValueError(
                "observed_at cannot be earlier than occurred_at"
            )

        object.__setattr__(
            self,
            "occurred_at",
            occurred_at,
        )

        object.__setattr__(
            self,
            "observed_at",
            observed_at,
        )

        if not isinstance(
            self.payload,
            Mapping,
        ):
            raise TypeError(
                "payload must be a mapping"
            )

        if not isinstance(
            self.metadata,
            Mapping,
        ):
            raise TypeError(
                "metadata must be a mapping"
            )

        canonical_payload = dict(
            _canonicalize(self.payload)
        )

        canonical_metadata = dict(
            _canonicalize(self.metadata)
        )

        object.__setattr__(
            self,
            "payload",
            MappingProxyType(
                canonical_payload
            ),
        )

        object.__setattr__(
            self,
            "metadata",
            MappingProxyType(
                canonical_metadata
            ),
        )

        if self.ordering_key is not None:
            object.__setattr__(
                self,
                "ordering_key",
                _required_text(
                    self.ordering_key,
                    "ordering_key",
                    255,
                ),
            )

        if self.sequence is not None:
            if not isinstance(
                self.sequence,
                int,
            ):
                raise TypeError(
                    "sequence must be int or None"
                )

            if self.sequence < 0:
                raise ValueError(
                    "sequence must be >= 0"
                )

        if self.idempotency_key is not None:
            object.__setattr__(
                self,
                "idempotency_key",
                _required_text(
                    self.idempotency_key,
                    "idempotency_key",
                    255,
                ),
            )

        if (
            self.sequence is not None
            and self.ordering_key is None
        ):
            raise ValueError(
                "sequence requires ordering_key"
            )

    @classmethod
    def create(
        cls,
        *,
        event_type: str,
        schema_name: str,
        schema_version: int,
        event_version: int,
        tenant_id: UUID,
        producer_id: UUID,
        payload: Mapping[str, Any],
        correlation_id: UUID | None = None,
        causation_id: UUID | None = None,
        occurred_at: datetime | None = None,
        observed_at: datetime | None = None,
        trace_context: EventTraceContext | None = None,
        ordering_key: str | None = None,
        sequence: int | None = None,
        idempotency_key: str | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> "EventEnvelope":
        now = _utc_now()

        return cls(
            event_id=uuid4(),
            event_type=event_type,
            schema_name=schema_name,
            schema_version=schema_version,
            event_version=event_version,
            tenant_id=tenant_id,
            producer_id=producer_id,
            correlation_id=correlation_id or uuid4(),
            causation_id=causation_id,
            occurred_at=occurred_at or now,
            observed_at=observed_at or now,
            payload=payload,
            trace_context=trace_context,
            ordering_key=ordering_key,
            sequence=sequence,
            idempotency_key=idempotency_key,
            metadata=metadata or {},
        )

    @property
    def contract_key(self) -> str:
        return (
            f"{self.schema_name}:"
            f"{self.schema_version}:"
            f"{self.event_type}"
        )

    @property
    def identity_key(self) -> tuple[UUID, str]:
        return (
            self.tenant_id,
            str(self.event_id),
        )

    @property
    def immutable_fingerprint(self) -> str:
        material = self.to_dict()

        return sha256(
            _canonical_json(material).encode(
                "utf-8"
            )
        ).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": str(self.event_id),
            "event_type": self.event_type,
            "schema_name": self.schema_name,
            "schema_version": self.schema_version,
            "event_version": self.event_version,
            "tenant_id": str(self.tenant_id),
            "producer_id": str(self.producer_id),
            "correlation_id": str(
                self.correlation_id
            ),
            "causation_id": (
                str(self.causation_id)
                if self.causation_id is not None
                else None
            ),
            "occurred_at": self.occurred_at.isoformat(),
            "observed_at": self.observed_at.isoformat(),
            "payload": _canonicalize(self.payload),
            "trace_context": (
                self.trace_context.to_dict()
                if self.trace_context is not None
                else None
            ),
            "ordering_key": self.ordering_key,
            "sequence": self.sequence,
            "idempotency_key": self.idempotency_key,
            "metadata": _canonicalize(self.metadata),
        }

    def serialize(self) -> str:
        return _canonical_json(
            self.to_dict()
        )

    def assert_tenant(
        self,
        tenant_id: UUID,
    ) -> None:
        _validate_uuid(
            tenant_id,
            "tenant_id",
        )

        if tenant_id != self.tenant_id:
            raise EventTenantViolation(
                "event tenant does not match requested tenant"
            )

    def verify_fingerprint(
        self,
        fingerprint: str,
    ) -> bool:
        if not isinstance(
            fingerprint,
            str,
        ):
            raise TypeError(
                "fingerprint must be string"
            )

        return (
            self.immutable_fingerprint
            == fingerprint
        )


__all__ = [
    "EventDomainError",
    "EventValidationError",
    "EventTenantViolation",
    "EventMutationError",
    "EventSerializationError",
    "EventTraceContext",
    "EventEnvelope",
]
