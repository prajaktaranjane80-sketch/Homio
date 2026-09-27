"""
CORE-004 T12 — Domain Event Integration

Owns:
- inventory-created
- inventory-updated
- availability-changed
- lifecycle-changed
- reservation-state-changed
- allocation-state-changed
- provenance-change
- CORE-002 event-contract projection

Does NOT own:
- event transport
- event bus
- Kafka
- outbox
- event persistence
- delivery retry
- consumer registry
- REOS state
- ACRL state

CORE-002 remains the event-platform authority.

CORE-004 creates an immutable event specification that can be projected
to the existing CORE-002 event contract.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
import hashlib
import json
from typing import Any, Mapping


class InventoryEventIntegrationError(
    ValueError
):
    """Base CORE-004 event integration error."""


class InventoryEventValidationError(
    InventoryEventIntegrationError
):
    """Raised when an event contract is malformed."""


class InventoryEventConflictError(
    InventoryEventIntegrationError
):
    """Raised when an event identity conflicts."""


class InventoryDomainEventType(str, Enum):
    INVENTORY_CREATED = "INVENTORY_CREATED"
    INVENTORY_UPDATED = "INVENTORY_UPDATED"
    INVENTORY_AVAILABILITY_CHANGED = (
        "INVENTORY_AVAILABILITY_CHANGED"
    )
    INVENTORY_LIFECYCLE_CHANGED = (
        "INVENTORY_LIFECYCLE_CHANGED"
    )
    INVENTORY_RESERVATION_STATE_CHANGED = (
        "INVENTORY_RESERVATION_STATE_CHANGED"
    )
    INVENTORY_ALLOCATION_STATE_CHANGED = (
        "INVENTORY_ALLOCATION_STATE_CHANGED"
    )
    INVENTORY_PROVENANCE_CHANGED = (
        "INVENTORY_PROVENANCE_CHANGED"
    )


CORE_004_EVENT_SCHEMA_VERSION = 1
CORE_004_EVENT_PRODUCER = "CORE-004"


def _text(
    value: str,
    name: str,
) -> str:
    if not isinstance(
        value,
        str,
    ):
        raise InventoryEventValidationError(
            f"{name} must be string."
        )

    value = value.strip()

    if not value:
        raise InventoryEventValidationError(
            f"{name} cannot be empty."
        )

    return value


def _time(
    value: datetime,
    name: str,
) -> datetime:
    if not isinstance(
        value,
        datetime,
    ):
        raise InventoryEventValidationError(
            f"{name} must be datetime."
        )

    if (
        value.tzinfo is None
        or value.utcoffset() is None
    ):
        raise InventoryEventValidationError(
            f"{name} must be timezone-aware."
        )

    return value.astimezone(
        timezone.utc
    )


def _canonicalize(
    value: Any,
) -> Any:
    if isinstance(
        value,
        Enum,
    ):
        return value.value

    if isinstance(
        value,
        datetime,
    ):
        return _time(
            value,
            "datetime",
        ).isoformat()

    if isinstance(
        value,
        Mapping,
    ):
        return {
            str(key): _canonicalize(item)
            for key, item in sorted(
                value.items(),
                key=lambda pair: str(pair[0]),
            )
        }

    if isinstance(
        value,
        (list, tuple),
    ):
        return [
            _canonicalize(item)
            for item in value
        ]

    if (
        value is None
        or isinstance(
            value,
            (str, int, float, bool),
        )
    ):
        return value

    raise InventoryEventValidationError(
        "Unsupported event payload value type: "
        f"{type(value).__name__}"
    )


@dataclass(frozen=True, slots=True)
class InventoryDomainEvent:
    """
    Immutable CORE-004 event specification.

    This is the event-domain boundary only.

    No event is published or persisted by this object.
    """

    event_id: str
    tenant_id: str
    inventory_id: str
    inventory_version: int
    event_type: InventoryDomainEventType
    schema_version: int
    correlation_id: str
    causation_id: str | None
    idempotency_key: str
    payload: Mapping[str, Any]
    occurred_at: datetime
    producer: str = CORE_004_EVENT_PRODUCER

    def __post_init__(self) -> None:
        for field_name in (
            "event_id",
            "tenant_id",
            "inventory_id",
            "correlation_id",
            "idempotency_key",
            "producer",
        ):
            object.__setattr__(
                self,
                field_name,
                _text(
                    getattr(
                        self,
                        field_name,
                    ),
                    field_name,
                ),
            )

        if self.causation_id is not None:
            object.__setattr__(
                self,
                "causation_id",
                _text(
                    self.causation_id,
                    "causation_id",
                ),
            )

        if not isinstance(
            self.inventory_version,
            int,
        ) or self.inventory_version < 1:
            raise InventoryEventValidationError(
                "inventory_version must be >= 1."
            )

        if not isinstance(
            self.event_type,
            InventoryDomainEventType,
        ):
            raise InventoryEventValidationError(
                "event_type must be InventoryDomainEventType."
            )

        if (
            not isinstance(
                self.schema_version,
                int,
            )
            or self.schema_version < 1
        ):
            raise InventoryEventValidationError(
                "schema_version must be >= 1."
            )

        if not isinstance(
            self.payload,
            Mapping,
        ):
            raise InventoryEventValidationError(
                "payload must be mapping."
            )

        normalized_payload = {
            str(key): _canonicalize(item)
            for key, item in self.payload.items()
        }

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

    @classmethod
    def create(
        cls,
        *,
        tenant_id: str,
        inventory_id: str,
        inventory_version: int,
        event_type: InventoryDomainEventType,
        correlation_id: str,
        idempotency_key: str,
        payload: Mapping[str, Any],
        causation_id: str | None = None,
        event_id: str,
        occurred_at: datetime | None = None,
        schema_version: int = (
            CORE_004_EVENT_SCHEMA_VERSION
        ),
        producer: str = CORE_004_EVENT_PRODUCER,
    ) -> "InventoryDomainEvent":
        return cls(
            event_id=event_id,
            tenant_id=tenant_id,
            inventory_id=inventory_id,
            inventory_version=inventory_version,
            event_type=event_type,
            schema_version=schema_version,
            correlation_id=correlation_id,
            causation_id=causation_id,
            idempotency_key=idempotency_key,
            payload=payload,
            occurred_at=(
                datetime.now(timezone.utc)
                if occurred_at is None
                else occurred_at
            ),
            producer=producer,
        )

    @property
    def identity_key(self) -> tuple[str, str, str]:
        """
        Tenant + inventory + idempotency defines event identity.
        """
        return (
            self.tenant_id,
            self.inventory_id,
            self.idempotency_key,
        )

    @property
    def fingerprint(self) -> str:
        payload = {
            "event_id": self.event_id,
            "tenant_id": self.tenant_id,
            "inventory_id": self.inventory_id,
            "inventory_version": (
                self.inventory_version
            ),
            "event_type": self.event_type.value,
            "schema_version": self.schema_version,
            "correlation_id": self.correlation_id,
            "causation_id": self.causation_id,
            "idempotency_key": self.idempotency_key,
            "payload": self.payload,
            "occurred_at": (
                self.occurred_at.isoformat()
            ),
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
        tenant_id: str,
    ) -> None:
        if _text(
            tenant_id,
            "tenant_id",
        ) != self.tenant_id:
            raise InventoryEventValidationError(
                "Event tenant boundary violation."
            )

    def assert_compatible(
        self,
        other: "InventoryDomainEvent",
    ) -> None:
        if not isinstance(
            other,
            InventoryDomainEvent,
        ):
            raise InventoryEventValidationError(
                "other must be InventoryDomainEvent."
            )

        if self.identity_key != other.identity_key:
            raise InventoryEventConflictError(
                "Domain event identities differ."
            )

        if self.fingerprint != other.fingerprint:
            raise InventoryEventConflictError(
                "Same event identity contains conflicting payload."
            )

    def to_core002_payload(
        self,
    ) -> dict[str, Any]:
        """
        Canonical projection into the existing CORE-002 Event Platform
        contract.

        This is only a projection. It does not publish the event.
        """
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "schema_version": self.schema_version,
            "tenant_id": self.tenant_id,
            "producer": self.producer,
            "correlation_id": self.correlation_id,
            "causation_id": self.causation_id,
            "occurred_at": (
                self.occurred_at.isoformat()
            ),
            "idempotency_key": self.idempotency_key,
            "inventory_id": self.inventory_id,
            "inventory_version": (
                self.inventory_version
            ),
            "payload": dict(
                self.payload
            ),
            "fingerprint": self.fingerprint,
        }

    def to_dict(
        self,
    ) -> dict[str, Any]:
        return self.to_core002_payload()


def inventory_created_event(
    *,
    event_id: str,
    tenant_id: str,
    inventory_id: str,
    inventory_version: int,
    correlation_id: str,
    idempotency_key: str,
    payload: Mapping[str, Any],
    occurred_at: datetime | None = None,
) -> InventoryDomainEvent:
    return InventoryDomainEvent.create(
        event_id=event_id,
        tenant_id=tenant_id,
        inventory_id=inventory_id,
        inventory_version=inventory_version,
        event_type=(
            InventoryDomainEventType.INVENTORY_CREATED
        ),
        correlation_id=correlation_id,
        idempotency_key=idempotency_key,
        payload=payload,
        occurred_at=occurred_at,
    )


def inventory_updated_event(
    *,
    event_id: str,
    tenant_id: str,
    inventory_id: str,
    inventory_version: int,
    correlation_id: str,
    idempotency_key: str,
    payload: Mapping[str, Any],
    occurred_at: datetime | None = None,
) -> InventoryDomainEvent:
    return InventoryDomainEvent.create(
        event_id=event_id,
        tenant_id=tenant_id,
        inventory_id=inventory_id,
        inventory_version=inventory_version,
        event_type=(
            InventoryDomainEventType.INVENTORY_UPDATED
        ),
        correlation_id=correlation_id,
        idempotency_key=idempotency_key,
        payload=payload,
        occurred_at=occurred_at,
    )


def inventory_availability_changed_event(
    *,
    event_id: str,
    tenant_id: str,
    inventory_id: str,
    inventory_version: int,
    correlation_id: str,
    idempotency_key: str,
    payload: Mapping[str, Any],
    occurred_at: datetime | None = None,
) -> InventoryDomainEvent:
    return InventoryDomainEvent.create(
        event_id=event_id,
        tenant_id=tenant_id,
        inventory_id=inventory_id,
        inventory_version=inventory_version,
        event_type=(
            InventoryDomainEventType
            .INVENTORY_AVAILABILITY_CHANGED
        ),
        correlation_id=correlation_id,
        idempotency_key=idempotency_key,
        payload=payload,
        occurred_at=occurred_at,
    )


def inventory_lifecycle_changed_event(
    *,
    event_id: str,
    tenant_id: str,
    inventory_id: str,
    inventory_version: int,
    correlation_id: str,
    idempotency_key: str,
    payload: Mapping[str, Any],
    occurred_at: datetime | None = None,
) -> InventoryDomainEvent:
    return InventoryDomainEvent.create(
        event_id=event_id,
        tenant_id=tenant_id,
        inventory_id=inventory_id,
        inventory_version=inventory_version,
        event_type=(
            InventoryDomainEventType
            .INVENTORY_LIFECYCLE_CHANGED
        ),
        correlation_id=correlation_id,
        idempotency_key=idempotency_key,
        payload=payload,
        occurred_at=occurred_at,
    )


def inventory_reservation_state_changed_event(
    *,
    event_id: str,
    tenant_id: str,
    inventory_id: str,
    inventory_version: int,
    correlation_id: str,
    idempotency_key: str,
    payload: Mapping[str, Any],
    occurred_at: datetime | None = None,
) -> InventoryDomainEvent:
    return InventoryDomainEvent.create(
        event_id=event_id,
        tenant_id=tenant_id,
        inventory_id=inventory_id,
        inventory_version=inventory_version,
        event_type=(
            InventoryDomainEventType
            .INVENTORY_RESERVATION_STATE_CHANGED
        ),
        correlation_id=correlation_id,
        idempotency_key=idempotency_key,
        payload=payload,
        occurred_at=occurred_at,
    )


def inventory_allocation_state_changed_event(
    *,
    event_id: str,
    tenant_id: str,
    inventory_id: str,
    inventory_version: int,
    correlation_id: str,
    idempotency_key: str,
    payload: Mapping[str, Any],
    occurred_at: datetime | None = None,
) -> InventoryDomainEvent:
    return InventoryDomainEvent.create(
        event_id=event_id,
        tenant_id=tenant_id,
        inventory_id=inventory_id,
        inventory_version=inventory_version,
        event_type=(
            InventoryDomainEventType
            .INVENTORY_ALLOCATION_STATE_CHANGED
        ),
        correlation_id=correlation_id,
        idempotency_key=idempotency_key,
        payload=payload,
        occurred_at=occurred_at,
    )


def inventory_provenance_changed_event(
    *,
    event_id: str,
    tenant_id: str,
    inventory_id: str,
    inventory_version: int,
    correlation_id: str,
    idempotency_key: str,
    payload: Mapping[str, Any],
    occurred_at: datetime | None = None,
) -> InventoryDomainEvent:
    return InventoryDomainEvent.create(
        event_id=event_id,
        tenant_id=tenant_id,
        inventory_id=inventory_id,
        inventory_version=inventory_version,
        event_type=(
            InventoryDomainEventType
            .INVENTORY_PROVENANCE_CHANGED
        ),
        correlation_id=correlation_id,
        idempotency_key=idempotency_key,
        payload=payload,
        occurred_at=occurred_at,
    )


def compare_event_identity(
    left: InventoryDomainEvent,
    right: InventoryDomainEvent,
) -> None:
    left.assert_compatible(
        right
    )


__all__ = [
    "InventoryEventIntegrationError",
    "InventoryEventValidationError",
    "InventoryEventConflictError",
    "InventoryDomainEventType",
    "CORE_004_EVENT_SCHEMA_VERSION",
    "CORE_004_EVENT_PRODUCER",
    "InventoryDomainEvent",
    "inventory_created_event",
    "inventory_updated_event",
    "inventory_availability_changed_event",
    "inventory_lifecycle_changed_event",
    "inventory_reservation_state_changed_event",
    "inventory_allocation_state_changed_event",
    "inventory_provenance_changed_event",
    "compare_event_identity",
]
