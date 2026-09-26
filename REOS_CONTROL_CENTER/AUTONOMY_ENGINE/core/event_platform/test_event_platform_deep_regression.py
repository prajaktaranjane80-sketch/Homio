from __future__ import annotations

from datetime import datetime, timezone
from types import MappingProxyType
from uuid import uuid4

import pytest

from .event_acrl_contract import (
    ACRLEventContractError,
    ACRLIntegrationBoundary,
)
from .event_contract import (
    EventContract,
    EventContractError,
    EventContractRegistry,
    UnsupportedEventVersionError,
)
from .event_delivery import (
    DeliveryAuthorizationError,
    DeliveryFailureClass,
    DeliveryPolicy,
    DeliveryStatus,
    DuplicateDeliveryError,
    EventDeliveryCoordinator,
)
from .event_domain import (
    EventEnvelope,
    EventTraceContext,
)
from .event_observability import (
    EvidenceType,
    EventEvidenceFactory,
    validate_evidence_tenant,
)
from .event_reos_contract import (
    REOSEventContractError,
    REOSIntegrationBoundary,
    REOSIntegrationContract,
)
from .event_security import (
    CrossTenantEventError,
    EventIntegrityError,
    EventSecurityBoundary,
    ProducerAuthorizationError,
)
from .event_transaction import (
    InvalidPublicationStateError,
    PublicationState,
    PublicationStateMachine,
    build_publication_contract,
)


def make_event(
    *,
    tenant_id=None,
    producer_id=None,
    event_type="LEAD.CREATED",
    schema_version=1,
    event_version=1,
    payload=None,
    ordering_key=None,
    sequence=None,
    idempotency_key="idem-001",
):
    now = datetime.now(timezone.utc)

    return EventEnvelope(
        event_id=uuid4(),
        event_type=event_type,
        schema_name="reos.test",
        schema_version=schema_version,
        event_version=event_version,
        tenant_id=tenant_id or uuid4(),
        producer_id=producer_id or uuid4(),
        correlation_id=uuid4(),
        causation_id=None,
        occurred_at=now,
        observed_at=now,
        payload=payload or {
            "lead_id": "L-001",
            "source": "test",
        },
        trace_context=EventTraceContext(
            trace_id="trace-001",
            span_id="span-001",
        ),
        ordering_key=ordering_key,
        sequence=sequence,
        idempotency_key=idempotency_key,
        metadata={"test": "deep-regression"},
    )


def make_contract(
    *,
    event_type="LEAD.CREATED",
    schema_version=1,
    event_version=1,
    allow_additional_fields=True,
):
    return EventContract(
        schema_name="reos.test",
        event_type=event_type,
        schema_version=schema_version,
        event_version=event_version,
        required_fields=(
            "lead_id",
            "source",
        ),
        field_types={
            "lead_id": "string",
            "source": "string",
        },
        allow_additional_fields=allow_additional_fields,
    )


class FakeIdempotency:
    def __init__(self):
        self.applied = set()
        self.mark_calls = 0

    def already_applied(
        self,
        *,
        tenant_id,
        consumer_id,
        idempotency_key,
    ):
        return (
            tenant_id,
            consumer_id,
            idempotency_key,
        ) in self.applied

    def mark_applied(
        self,
        *,
        tenant_id,
        consumer_id,
        idempotency_key,
    ):
        self.mark_calls += 1
        self.applied.add(
            (
                tenant_id,
                consumer_id,
                idempotency_key,
            )
        )


# ---------------------------------------------------------------------------
# CONTRACT IMMUTABILITY + SCHEMA EVOLUTION
# ---------------------------------------------------------------------------


def test_contract_default_field_types_is_usable():
    contract = EventContract(
        schema_name="reos.test",
        event_type="PING.EVENT",
        schema_version=1,
        event_version=1,
    )

    assert contract.field_types == {}


def test_contract_field_types_are_immutable():
    contract = make_contract()

    assert isinstance(
        contract.field_types,
        MappingProxyType,
    )

    with pytest.raises(TypeError):
        contract.field_types["new"] = "string"


def test_contract_required_field_duplicates_are_rejected():
    with pytest.raises(ValueError, match="duplicates"):
        EventContract(
            schema_name="reos.test",
            event_type="LEAD.CREATED",
            schema_version=1,
            event_version=1,
            required_fields=(
                "lead_id",
                "lead_id",
            ),
            field_types={
                "lead_id": "string",
            },
        )


def test_contract_boolean_versions_are_rejected():
    with pytest.raises(TypeError):
        EventContract(
            schema_name="reos.test",
            event_type="LEAD.CREATED",
            schema_version=True,
            event_version=1,
        )

    with pytest.raises(TypeError):
        EventContract(
            schema_name="reos.test",
            event_type="LEAD.CREATED",
            schema_version=1,
            event_version=False,
        )


def test_required_field_must_have_type_definition():
    with pytest.raises(
        ValueError,
        match="missing type definitions",
    ):
        EventContract(
            schema_name="reos.test",
            event_type="LEAD.CREATED",
            schema_version=1,
            event_version=1,
            required_fields=("lead_id",),
            field_types={},
        )


def test_contract_fingerprint_changes_on_definition_change():
    contract_v1 = make_contract()

    contract_v2 = EventContract(
        schema_name="reos.test",
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
            "score": "number",
        },
    )

    assert (
        contract_v1.fingerprint
        != contract_v2.fingerprint
    )


def test_schema_version_evolution_requires_explicit_contract():
    registry = EventContractRegistry()

    v1 = make_contract(
        schema_version=1,
        event_version=1,
    )

    registry.register(v1)

    event_v2 = make_event(
        schema_version=2,
        event_version=1,
    )

    with pytest.raises(UnsupportedEventVersionError):
        registry.validate(event_v2)


# ---------------------------------------------------------------------------
# DELIVERY
# ---------------------------------------------------------------------------


def test_delivery_success_acknowledges_and_marks_idempotency():
    tenant_id = uuid4()
    consumer_id = uuid4()

    registry = EventContractRegistry()
    registry.register(make_contract())

    idem = FakeIdempotency()

    coordinator = EventDeliveryCoordinator(
        contracts=registry,
        idempotency=idem,
        tenant_authorizer=lambda tenant, consumer: (
            tenant == tenant_id
            and consumer == consumer_id
        ),
    )

    calls = []

    result = coordinator.dispatch(
        event=make_event(
            tenant_id=tenant_id,
        ),
        consumer_id=consumer_id,
        handler=lambda event: calls.append(
            event.event_id
        ),
    )

    assert result.status is DeliveryStatus.ACKNOWLEDGED
    assert len(calls) == 1
    assert idem.mark_calls == 1


def test_duplicate_delivery_never_reaches_consumer():
    tenant_id = uuid4()
    consumer_id = uuid4()

    registry = EventContractRegistry()
    registry.register(make_contract())

    idem = FakeIdempotency()

    event = make_event(
        tenant_id=tenant_id,
        idempotency_key="same-delivery",
    )

    idem.mark_applied(
        tenant_id=tenant_id,
        consumer_id=consumer_id,
        idempotency_key="same-delivery",
    )

    coordinator = EventDeliveryCoordinator(
        contracts=registry,
        idempotency=idem,
        tenant_authorizer=lambda *_: True,
    )

    calls = []

    with pytest.raises(DuplicateDeliveryError):
        coordinator.dispatch(
            event=event,
            consumer_id=consumer_id,
            handler=lambda event: calls.append(event),
        )

    assert calls == []


def test_delivery_failure_does_not_mark_idempotency():
    tenant_id = uuid4()
    consumer_id = uuid4()

    registry = EventContractRegistry()
    registry.register(make_contract())

    idem = FakeIdempotency()

    coordinator = EventDeliveryCoordinator(
        contracts=registry,
        idempotency=idem,
        tenant_authorizer=lambda *_: True,
    )

    result = coordinator.dispatch(
        event=make_event(
            tenant_id=tenant_id,
        ),
        consumer_id=consumer_id,
        handler=lambda event: (_ for _ in ()).throw(
            RuntimeError("transient failure")
        ),
    )

    assert result.status is DeliveryStatus.RETRYABLE_FAILURE
    assert result.failure_class is DeliveryFailureClass.TRANSIENT
    assert idem.mark_calls == 0


def test_cross_tenant_delivery_fails_closed():
    tenant_id = uuid4()
    consumer_id = uuid4()

    registry = EventContractRegistry()
    registry.register(make_contract())

    coordinator = EventDeliveryCoordinator(
        contracts=registry,
        idempotency=FakeIdempotency(),
        tenant_authorizer=lambda *_: False,
    )

    with pytest.raises(DeliveryAuthorizationError):
        coordinator.dispatch(
            event=make_event(
                tenant_id=tenant_id,
            ),
            consumer_id=consumer_id,
            handler=lambda event: None,
        )


def test_delivery_policy_never_retries_authorization():
    policy = DeliveryPolicy(max_attempts=10)

    assert not policy.should_retry(
        attempt_number=1,
        failure_class=DeliveryFailureClass.AUTHORIZATION,
    )


# ---------------------------------------------------------------------------
# TRANSACTION / OUTBOX BOUNDARY
# ---------------------------------------------------------------------------


def test_publication_state_machine_enforces_terminal_states():
    assert (
        PublicationStateMachine.transition(
            PublicationState.CREATED,
            PublicationState.COMMITTED,
        )
        is PublicationState.COMMITTED
    )

    assert (
        PublicationStateMachine.transition(
            PublicationState.COMMITTED,
            PublicationState.RECOVERABLE,
        )
        is PublicationState.RECOVERABLE
    )

    with pytest.raises(InvalidPublicationStateError):
        PublicationStateMachine.transition(
            PublicationState.PUBLISHED,
            PublicationState.COMMITTED,
        )


def test_publication_contract_preserves_tenant_and_fingerprint():
    publication_id = uuid4()
    event_id = uuid4()
    tenant_id = uuid4()

    contract = build_publication_contract(
        publication_id=publication_id,
        event_id=event_id,
        tenant_id=tenant_id,
        event_fingerprint="fingerprint-001",
    )

    assert contract.publication_id == publication_id
    assert contract.event_id == event_id
    assert contract.tenant_id == tenant_id
    assert contract.event_fingerprint == "fingerprint-001"
    assert contract.state is PublicationState.CREATED


def test_publication_contract_rejects_empty_fingerprint():
    with pytest.raises(ValueError):
        build_publication_contract(
            publication_id=uuid4(),
            event_id=uuid4(),
            tenant_id=uuid4(),
            event_fingerprint="",
        )


# ---------------------------------------------------------------------------
# OBSERVABILITY / EVIDENCE
# ---------------------------------------------------------------------------


def test_evidence_factory_propagates_event_context():
    event = make_event()

    evidence = EventEvidenceFactory().create(
        evidence_id=uuid4(),
        event=event,
        evidence_type=EvidenceType.ACKNOWLEDGED,
        consumer_id=uuid4(),
    )

    assert evidence.event_id == event.event_id
    assert evidence.tenant_id == event.tenant_id
    assert evidence.producer_id == event.producer_id
    assert evidence.correlation_id == event.correlation_id
    assert evidence.causation_id == event.causation_id
    assert evidence.trace_id == "trace-001"


def test_evidence_cross_tenant_mismatch_is_rejected():
    event = make_event()

    evidence = EventEvidenceFactory().create(
        evidence_id=uuid4(),
        event=event,
        evidence_type=EvidenceType.DISPATCHED,
    )

    object.__setattr__(
        evidence,
        "tenant_id",
        uuid4(),
    )

    with pytest.raises(
        ValueError,
        match="tenant",
    ):
        validate_evidence_tenant(
            evidence=evidence,
            event=event,
        )


# ---------------------------------------------------------------------------
# REOS INTEGRATION
# ---------------------------------------------------------------------------


def test_reos_contract_cannot_own_canonical_state():
    with pytest.raises(REOSEventContractError):
        REOSIntegrationContract(
            gate_name="CORE-002",
            task_name="CORE-002-T01",
            verification_command="verify-all",
            canonical_state_owned_externally=False,
        )


def test_reos_boundary_is_discover_and_verify_only():
    calls = []

    boundary = REOSIntegrationBoundary(
        discover_contract=lambda: {
            "gate": "CORE-002",
        },
        verify=lambda command: calls.append(command) or True,
    )

    assert boundary.discover()["gate"] == "CORE-002"
    assert boundary.verify("verify-all") is True
    assert calls == ["verify-all"]


def test_reos_boundary_rejects_invalid_discovery():
    boundary = REOSIntegrationBoundary(
        discover_contract=lambda: "invalid",
        verify=lambda command: True,
    )

    with pytest.raises(REOSEventContractError):
        boundary.discover()


# ---------------------------------------------------------------------------
# ACRL INTEGRATION
# ---------------------------------------------------------------------------


def test_acrl_reconstruction_boundary_returns_mapping():
    event_id = uuid4()

    boundary = ACRLIntegrationBoundary(
        reconstruct=lambda value: {
            "event_id": str(value),
        },
        discover_dependencies=lambda key: [
            "CORE-001",
            "CORE-002",
        ],
        detect_drift=lambda expected, actual: (
            expected != actual
        ),
    )

    result = boundary.reconstruct_event(event_id)

    assert result["event_id"] == str(event_id)


def test_acrl_rejects_invalid_reconstruction_result():
    boundary = ACRLIntegrationBoundary(
        reconstruct=lambda value: "invalid",
        discover_dependencies=lambda key: [],
        detect_drift=lambda expected, actual: False,
    )

    with pytest.raises(ACRLEventContractError):
        boundary.reconstruct_event(uuid4())


def test_acrl_dependency_discovery_is_deterministic_tuple():
    boundary = ACRLIntegrationBoundary(
        reconstruct=lambda value: {},
        discover_dependencies=lambda key: [
            "CORE-001",
            "CORE-002",
        ],
        detect_drift=lambda expected, actual: False,
    )

    assert boundary.dependencies(
        "reos.test:LEAD.CREATED"
    ) == (
        "CORE-001",
        "CORE-002",
    )


# ---------------------------------------------------------------------------
# SECURITY
# ---------------------------------------------------------------------------


def test_producer_authorization_is_enforced():
    boundary = EventSecurityBoundary(
        producer_authorizer=lambda *_: False,
        consumer_authorizer=lambda *_: True,
    )

    with pytest.raises(ProducerAuthorizationError):
        boundary.validate_producer(
            event=make_event(),
        )


def test_consumer_cross_tenant_boundary_is_enforced():
    event = make_event(
        tenant_id=uuid4(),
    )

    boundary = EventSecurityBoundary(
        producer_authorizer=lambda *_: True,
        consumer_authorizer=lambda *_: True,
    )

    with pytest.raises(CrossTenantEventError):
        boundary.validate_consumer(
            event=event,
            consumer_id=uuid4(),
            consumer_tenant_id=uuid4(),
        )


def test_event_integrity_detects_tampering():
    event = make_event()

    boundary = EventSecurityBoundary(
        producer_authorizer=lambda *_: True,
        consumer_authorizer=lambda *_: True,
    )

    digest = boundary.integrity_digest(event)

    tampered_payload = {
        "lead_id": "L-TAMPERED",
        "source": "test",
    }

    tampered_event = make_event(
        tenant_id=event.tenant_id,
        producer_id=event.producer_id,
        payload=tampered_payload,
    )

    with pytest.raises(EventIntegrityError):
        boundary.verify_integrity(
            event=tampered_event,
            expected_digest=digest,
        )


# ---------------------------------------------------------------------------
# DOMAIN IMMUTABILITY / CANONICAL SERIALIZATION
# ---------------------------------------------------------------------------


def test_event_payload_is_immutable():
    event = make_event()

    with pytest.raises(TypeError):
        event.payload["new"] = "value"


def test_event_metadata_is_immutable():
    event = make_event()

    with pytest.raises(TypeError):
        event.metadata["new"] = "value"


def test_event_fingerprint_is_deterministic():
    event_a = make_event(
        payload={
            "lead_id": "L-001",
            "source": "test",
        }
    )

    serialized_a = event_a.serialize()
    serialized_b = event_a.serialize()

    assert serialized_a == serialized_b
    assert (
        event_a.immutable_fingerprint
        == event_a.immutable_fingerprint
    )


def test_event_sequence_requires_ordering_key():
    with pytest.raises(
        ValueError,
        match="ordering_key",
    ):
        make_event(
            sequence=1,
            ordering_key=None,
        )
