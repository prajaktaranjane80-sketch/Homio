from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import pytest

from .event_domain import (
    EventEnvelope,
    EventTenantViolation,
)
from .event_contract import (
    EventContract,
    EventContractRegistry,
    EventContractError,
    UnknownEventTypeError,
)
from .event_ordering import (
    EventOrderingGuard,
    OutOfOrderEventError,
    StaleEventError,
)
from .event_resilience import (
    FailureClass,
    FailureDisposition,
    ResilienceBoundary,
)
from .event_security import (
    CrossTenantEventError,
    EventSecurityBoundary,
)
from .event_transport import (
    TransportRegistry,
    TransportAdapterError,
)
from .event_replay import (
    ReplayScope,
    ReplayAuthorizationBoundary,
    ReplayCoordinator,
    ReplayStatus,
)


AT = datetime(
    2026,
    9,
    26,
    10,
    0,
    tzinfo=timezone.utc,
)


def make_event(
    *,
    tenant_id=None,
    sequence=None,
    ordering_key=None,
):
    return EventEnvelope.create(
        event_type="LEAD.CREATED",
        schema_name="reos.lead",
        schema_version=1,
        event_version=1,
        tenant_id=(
            tenant_id
            if tenant_id is not None
            else uuid4()
        ),
        producer_id=uuid4(),
        correlation_id=uuid4(),
        payload={
            "lead_id": "L-001",
            "source": "brokerage",
        },
        occurred_at=AT,
        observed_at=AT,
        ordering_key=ordering_key,
        sequence=sequence,
        idempotency_key="L-001-created",
    )


def make_registry():
    registry = EventContractRegistry()

    registry.register(
        EventContract(
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
    )

    return registry


def test_contract_unknown_event_fails_closed():
    registry = EventContractRegistry()

    event = make_event()

    with pytest.raises(
        UnknownEventTypeError
    ):
        registry.validate(event)


def test_contract_conflict_is_rejected():
    registry = make_registry()

    conflicting = EventContract(
        schema_name="reos.lead",
        event_type="LEAD.CREATED",
        schema_version=1,
        event_version=1,
        required_fields=("other",),
        field_types={
            "other": "string",
        },
    )

    with pytest.raises(EventContractError):
        registry.register(conflicting)


def test_tenant_boundary_rejects_cross_tenant():
    tenant_a = uuid4()
    tenant_b = uuid4()

    event = make_event(
        tenant_id=tenant_a
    )

    with pytest.raises(
        EventTenantViolation
    ):
        event.assert_tenant(tenant_b)


def test_security_rejects_cross_tenant_consumer():
    tenant_a = uuid4()
    tenant_b = uuid4()
    consumer_id = uuid4()

    event = make_event(
        tenant_id=tenant_a
    )

    security = EventSecurityBoundary(
        producer_authorizer=lambda tenant, producer: True,
        consumer_authorizer=lambda tenant, consumer: True,
    )

    with pytest.raises(
        CrossTenantEventError
    ):
        security.validate_consumer(
            event=event,
            consumer_id=consumer_id,
            consumer_tenant_id=tenant_b,
        )


def test_ordering_rejects_stale_event():
    event = make_event(
        sequence=3,
        ordering_key="lead:L-001",
    )

    guard = EventOrderingGuard()

    decision = guard.validate(
        event=event,
        expected_next_sequence=4,
    )

    with pytest.raises(StaleEventError):
        guard.require_accepted(decision)


def test_ordering_rejects_future_event():
    event = make_event(
        sequence=5,
        ordering_key="lead:L-001",
    )

    guard = EventOrderingGuard()

    decision = guard.validate(
        event=event,
        expected_next_sequence=4,
    )

    with pytest.raises(OutOfOrderEventError):
        guard.require_accepted(decision)


def test_resilience_fail_closed_for_invalid_payload():
    boundary = ResilienceBoundary()

    result = boundary.handle_failure(
        event_id=uuid4(),
        tenant_id=uuid4(),
        attempt=1,
        exc=ValueError("invalid payload"),
    )

    assert (
        result.failure_class
        == FailureClass.PERMANENT
    )

    assert (
        result.disposition
        == FailureDisposition.DLQ
    )


def test_resilience_allows_transient_retry():
    boundary = ResilienceBoundary()

    result = boundary.handle_failure(
        event_id=uuid4(),
        tenant_id=uuid4(),
        attempt=1,
        exc=RuntimeError("temporary failure"),
    )

    assert (
        result.failure_class
        == FailureClass.TRANSIENT
    )

    assert (
        result.disposition
        == FailureDisposition.RETRY
    )


def test_resilience_exhausts_transient_failure():
    boundary = ResilienceBoundary()

    result = boundary.handle_failure(
        event_id=uuid4(),
        tenant_id=uuid4(),
        attempt=3,
        exc=RuntimeError("temporary failure"),
    )

    assert (
        result.disposition
        == FailureDisposition.DLQ
    )


def test_transport_registry_rejects_unknown_adapter():
    registry = TransportRegistry()

    with pytest.raises(
        TransportAdapterError
    ):
        registry.resolve("unknown")


def test_transport_registry_rejects_duplicate_adapter():
    registry = TransportRegistry()

    class Adapter:
        name = "test"

    registry.register(Adapter())

    with pytest.raises(
        TransportAdapterError
    ):
        registry.register(Adapter())


def test_replay_scope_rejects_duplicate_ids():
    event_id = uuid4()

    with pytest.raises(ValueError):
        ReplayScope(
            tenant_id=uuid4(),
            event_ids=(
                event_id,
                event_id,
            ),
            requested_by=uuid4(),
        )


def test_replay_rejects_unauthorized_request():
    scope = ReplayScope(
        tenant_id=uuid4(),
        event_ids=(uuid4(),),
        requested_by=uuid4(),
    )

    auth = ReplayAuthorizationBoundary(
        checker=lambda tenant, requester: False
    )

    coordinator = ReplayCoordinator(
        authorization=auth,
        duplicate_checker=lambda replay_id: False,
        mark_replay=lambda replay_id: None,
    )

    with pytest.raises(Exception):
        coordinator.create_request(
            scope=scope
        )


def test_replay_reports_partial_failure():
    tenant_id = uuid4()

    event_one = make_event(
        tenant_id=tenant_id,
        sequence=1,
        ordering_key="lead:L-001",
    )

    event_two = make_event(
        tenant_id=tenant_id,
        sequence=2,
        ordering_key="lead:L-001",
    )

    scope = ReplayScope(
        tenant_id=tenant_id,
        event_ids=(
            event_one.event_id,
            event_two.event_id,
        ),
        requested_by=uuid4(),
    )

    coordinator = ReplayCoordinator(
        authorization=ReplayAuthorizationBoundary(
            checker=lambda tenant, requester: True
        ),
        duplicate_checker=lambda replay_id: False,
        mark_replay=lambda replay_id: None,
    )

    request = coordinator.create_request(
        scope=scope
    )

    calls = []

    def handler(event):
        calls.append(event.event_id)

        if event.event_id == event_two.event_id:
            raise RuntimeError("consumer failure")

    result = coordinator.execute(
        request=request,
        events=(
            event_two,
            event_one,
        ),
        handler=handler,
    )

    assert (
        result.status
        == ReplayStatus.PARTIAL_FAILURE
    )

    assert event_one.event_id in (
        result.processed_event_ids
    )

    assert event_two.event_id in (
        result.failed_event_ids
    )
