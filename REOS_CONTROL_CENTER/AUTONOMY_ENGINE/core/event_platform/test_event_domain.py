from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import pytest

from .event_domain import (
    EventEnvelope,
    EventTenantViolation,
    EventTraceContext,
)
from .event_contract import (
    EventContract,
    EventContractRegistry,
    EventValidationError,
    UnknownEventTypeError,
)


AT = datetime(
    2026,
    9,
    26,
    10,
    0,
    tzinfo=timezone.utc,
)


@pytest.fixture
def tenant_id():
    return uuid4()


@pytest.fixture
def producer_id():
    return uuid4()


@pytest.fixture
def event(tenant_id, producer_id):
    return EventEnvelope.create(
        event_type="LEAD.CREATED",
        schema_name="reos.lead",
        schema_version=1,
        event_version=1,
        tenant_id=tenant_id,
        producer_id=producer_id,
        correlation_id=uuid4(),
        payload={
            "lead_id": "lead-001",
            "source": "brokerage",
        },
        occurred_at=AT,
        observed_at=AT,
        trace_context=EventTraceContext(
            trace_id="trace-001",
            span_id="span-001",
        ),
        idempotency_key="lead-created-001",
    )


def test_event_has_canonical_identity(event):
    assert event.event_id is not None
    assert event.event_type == "LEAD.CREATED"
    assert event.schema_name == "reos.lead"
    assert event.schema_version == 1
    assert event.event_version == 1


def test_event_is_tenant_scoped(event, tenant_id):
    event.assert_tenant(tenant_id)


def test_cross_tenant_event_is_rejected(event):
    with pytest.raises(EventTenantViolation):
        event.assert_tenant(uuid4())


def test_event_serialization_is_deterministic(event):
    assert event.serialize() == event.serialize()
    assert event.immutable_fingerprint == (
        event.immutable_fingerprint
    )


def test_event_fingerprint_detects_changed_event():
    tenant_id = uuid4()
    producer_id = uuid4()

    first = EventEnvelope.create(
        event_type="LEAD.CREATED",
        schema_name="reos.lead",
        schema_version=1,
        event_version=1,
        tenant_id=tenant_id,
        producer_id=producer_id,
        correlation_id=uuid4(),
        payload={"lead_id": "lead-001"},
        occurred_at=AT,
        observed_at=AT,
    )

    second = EventEnvelope.create(
        event_type="LEAD.CREATED",
        schema_name="reos.lead",
        schema_version=1,
        event_version=1,
        tenant_id=tenant_id,
        producer_id=producer_id,
        correlation_id=uuid4(),
        payload={"lead_id": "lead-002"},
        occurred_at=AT,
        observed_at=AT,
    )

    assert first.immutable_fingerprint != (
        second.immutable_fingerprint
    )


def test_event_contract_validates_payload(event):
    contract = EventContract(
        schema_name="reos.lead",
        event_type="LEAD.CREATED",
        schema_version=1,
        event_version=1,
        required_fields=(
            "lead_id",
            "source",
        ),
        field_types={
            "lead_id": "string",
            "source": "string",
        },
    )

    registry = EventContractRegistry()
    registry.register(contract)

    registry.validate(event)


def test_missing_required_field_is_rejected(
    tenant_id,
    producer_id,
):
    event = EventEnvelope.create(
        event_type="LEAD.CREATED",
        schema_name="reos.lead",
        schema_version=1,
        event_version=1,
        tenant_id=tenant_id,
        producer_id=producer_id,
        payload={
            "source": "brokerage",
        },
        occurred_at=AT,
        observed_at=AT,
    )

    contract = EventContract(
        schema_name="reos.lead",
        event_type="LEAD.CREATED",
        schema_version=1,
        event_version=1,
        required_fields=("lead_id",),
        field_types={
            "lead_id": "string",
        },
    )

    registry = EventContractRegistry()
    registry.register(contract)

    with pytest.raises(EventValidationError):
        registry.validate(event)


def test_unknown_event_contract_fails_closed(event):
    registry = EventContractRegistry()

    with pytest.raises(UnknownEventTypeError):
        registry.validate(event)


def test_same_contract_cannot_be_redefined():
    contract = EventContract(
        schema_name="reos.lead",
        event_type="LEAD.CREATED",
        schema_version=1,
        event_version=1,
        required_fields=("lead_id",),
        field_types={
            "lead_id": "string",
        },
    )

    registry = EventContractRegistry()
    registry.register(contract)

    registry.register(contract)

    conflicting = EventContract(
        schema_name="reos.lead",
        event_type="LEAD.CREATED",
        schema_version=1,
        event_version=1,
        required_fields=("lead_id", "source"),
        field_types={
            "lead_id": "string",
            "source": "string",
        },
    )

    with pytest.raises(Exception):
        registry.register(conflicting)
