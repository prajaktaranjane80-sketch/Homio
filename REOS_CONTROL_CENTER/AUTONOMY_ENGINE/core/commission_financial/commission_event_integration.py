from __future__ import annotations

from datetime import datetime
from typing import Any, Mapping
from uuid import UUID

from ..contract_primitives import fingerprint
from ..event_platform.event_contract import EventContractRegistry
from ..event_platform.event_domain import EventEnvelope

from .commission_event_contract import (
    COMMISSION_EVENT_DEFINITIONS,
    CORE008_EVENT_SCHEMA,
    CORE008_EVENT_SCHEMA_VERSION,
    CORE008_EVENT_VERSION,
    CommissionEventType,
    get_event_definition,
)


class CommissionEventIntegrationError(ValueError):
    """CORE-008 financial event integration error."""


def build_core008_event_registry() -> EventContractRegistry:
    """
    Register CORE-008 financial event contracts in the existing
    CORE-002 contract registry.

    This does not create a second event registry authority.
    """
    registry = EventContractRegistry()

    for definition in COMMISSION_EVENT_DEFINITIONS:
        registry.register(
            definition.contract()
        )

    return registry


class CommissionEventIntegration:
    """
    CORE-008 -> CORE-002 integration boundary.

    Responsibilities:
        - register CORE-008 event contracts
        - construct canonical EventEnvelope objects
        - derive deterministic idempotency keys
        - validate the resulting CORE-002 event

    Not responsible for:
        - transport
        - Kafka
        - outbox
        - persistence
        - replay
        - payment execution
        - ledger posting
        - Control Center state
        - ACRL state
    """

    def __init__(
        self,
        registry: EventContractRegistry | None = None,
    ) -> None:
        self.registry = (
            registry
            if registry is not None
            else build_core008_event_registry()
        )

    def contract_key(
        self,
        event_type: CommissionEventType,
    ) -> tuple[str, str, int, int]:
        return (
            CORE008_EVENT_SCHEMA,
            event_type.value,
            CORE008_EVENT_SCHEMA_VERSION,
            CORE008_EVENT_VERSION,
        )

    def validate_payload(
        self,
        event_type: CommissionEventType,
        payload: Mapping[str, Any],
    ) -> dict[str, Any]:
        if not isinstance(payload, Mapping):
            raise CommissionEventIntegrationError(
                "payload must be a mapping"
            )

        definition = get_event_definition(event_type)

        normalized = dict(payload)

        missing = [
            field
            for field in definition.required_fields
            if field not in normalized
        ]

        if missing:
            raise CommissionEventIntegrationError(
                "Missing required financial event fields: "
                + ", ".join(missing)
            )

        return normalized

    def idempotency_key(
        self,
        *,
        event_type: CommissionEventType,
        tenant_reference: str,
        source_id: str,
        source_fingerprint: str,
    ) -> str:
        if not all(
            isinstance(value, str) and value.strip()
            for value in (
                tenant_reference,
                source_id,
                source_fingerprint,
            )
        ):
            raise CommissionEventIntegrationError(
                "Idempotency inputs must be non-empty text"
            )

        return fingerprint(
            {
                "schema": CORE008_EVENT_SCHEMA,
                "event_type": event_type.value,
                "tenant_reference": tenant_reference.strip(),
                "source_id": source_id.strip(),
                "source_fingerprint": source_fingerprint.strip(),
            }
        )

    def create_event(
        self,
        *,
        event_type: CommissionEventType,
        tenant_id: UUID,
        producer_id: UUID,
        tenant_reference: str,
        source_id: str,
        source_fingerprint: str,
        payload: Mapping[str, Any],
        correlation_id: UUID | None = None,
        causation_id: UUID | None = None,
        occurred_at: datetime | None = None,
        observed_at: datetime | None = None,
    ) -> EventEnvelope:
        normalized = self.validate_payload(
            event_type,
            payload,
        )

        key = self.idempotency_key(
            event_type=event_type,
            tenant_reference=tenant_reference,
            source_id=source_id,
            source_fingerprint=source_fingerprint,
        )

        normalized.update(
            {
                "financial_source_id": source_id,
                "financial_source_fingerprint": source_fingerprint,
                "financial_tenant_reference": tenant_reference,
            }
        )

        event = EventEnvelope.create(
            event_type=event_type.value,
            schema_name=CORE008_EVENT_SCHEMA,
            schema_version=CORE008_EVENT_SCHEMA_VERSION,
            event_version=CORE008_EVENT_VERSION,
            tenant_id=tenant_id,
            producer_id=producer_id,
            payload=normalized,
            correlation_id=correlation_id,
            causation_id=causation_id,
            occurred_at=occurred_at,
            observed_at=observed_at,
            ordering_key=f"commission:{normalized['commission_id']}",
            idempotency_key=key,
            metadata={
                "core": "CORE-008",
                "integration": "CORE-008->CORE-002",
                "source_type": "commission_financial",
            },
        )

        self.registry.validate(event)

        return event

    def validate_event(
        self,
        event: EventEnvelope,
    ) -> None:
        self.registry.validate(event)


__all__ = [
    "CommissionEventIntegration",
    "CommissionEventIntegrationError",
    "build_core008_event_registry",
]
