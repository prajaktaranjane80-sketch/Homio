"""
CORE-003 Deep Contract Test Matrix

Coverage:
01 Event identity/domain
02 Tenant isolation
03 Serialization/fingerprint
04 Contract registration/validation
05 Unknown contract fail-closed
06 Ordering stale/future boundary
07 Resilience transient/permanent boundary
08 Transport registry boundary
09 Replay authorization/scope
10 Replay partial failure
11 Delivery boundary
12 Transaction/outbox boundary
13 Observability/evidence
14 REOS integration contract
15 ACRL integration contract
16 Security producer authorization boundary
17 Schema evolution/compatibility
18 Contract fingerprint immutability
19 Deep adversarial regression

Important:
CORE-003 does not reimplement:
- CORE-002 event engine
- transport registry
- delivery engine
- replay engine
- transaction/outbox
- producer authorization engine
- ACRL engine

Those responsibilities are tested here only through boundary invariants.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from .lead import (
    Lead,
    LeadPriority,
    LeadSource,
    LeadSourceType,
    LeadStatus,
    LeadValidationError,
)
from .lead_contract import (
    DEFAULT_LEAD_CONTRACT,
    LeadContract,
    LeadSchemaError,
)
from .lead_attribution import (
    AttributionValidationError,
    LeadAttribution,
)
from .lead_ownership import (
    LeadOwnerRole,
    LeadOwnership,
    OwnershipConflictError,
    OwnershipTenantViolation,
)
from .ownership_transfer import (
    OwnershipTransfer,
    OwnershipTransferValidationError,
    TransferReason,
)
from .lead_communication import (
    CommunicationChannel,
    CommunicationDirection,
    CommunicationEvidenceConflictError,
    LeadCommunicationEvidenceHook,
)
from .lead_fraud_handoff import (
    FraudHandoffPriority,
    FraudHandoffReason,
    FraudHandoffConflictError,
    LeadFraudHandoff,
)
from .lead_consistency import (
    LeadConcurrencyConflict,
    LeadConsistencySnapshot,
    LeadMutationPrecondition,
)
from .lead_security import (
    LeadCapability,
    LeadCapabilityViolation,
    LeadSecurityContext,
    LeadSecurityContextError,
    LeadTenantBoundaryViolation,
)
from .lead_acrl_contract import (
    LeadAcrlIntegrationContract,
    LeadAcrlPreconditionConflict,
    ReosLeadOperation,
)
from .lead_event_integration import (
    LeadDomainEvent,
    LeadDomainEventType,
    LeadEventConflictError,
    LeadEventValidationError,
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def make_lead(
    *,
    tenant_id=None,
    customer_id=None,
) -> Lead:
    return Lead.create(
        tenant_id=tenant_id or uuid4(),
        customer_id=customer_id or uuid4(),
        source=LeadSource(
            source_type=LeadSourceType.WEBSITE,
            source_id="website-001",
            campaign_id="campaign-001",
            channel="organic",
        ),
        metadata={
            "market": "international",
            "source_verified": True,
        },
    )


def make_ownership(
    lead: Lead,
    *,
    owner_id=None,
    revision: int = 0,
) -> LeadOwnership:
    return LeadOwnership(
        lead_id=lead.lead_id,
        tenant_id=lead.tenant_id,
        owner_id=owner_id or uuid4(),
        owner_role=LeadOwnerRole.AGENT,
        assigned_at=utc_now(),
        revision=revision,
    )


def make_security_context(
    tenant_id,
    capabilities=None,
) -> LeadSecurityContext:
    return LeadSecurityContext(
        tenant_id=tenant_id,
        actor_id=uuid4(),
        capabilities=frozenset(
            capabilities or {
                LeadCapability.READ_LEAD,
            }
        ),
        authorization_reference="core001-auth-001",
        issued_at=utc_now(),
    )


def make_precondition(
    lead: Lead,
    ownership: LeadOwnership | None,
    *,
    idempotency_key: str = "operation-001",
) -> LeadMutationPrecondition:
    return LeadMutationPrecondition(
        tenant_id=lead.tenant_id,
        lead_id=lead.lead_id,
        expected_lead_revision=lead.revision,
        expected_ownership_revision=(
            ownership.revision
            if ownership is not None
            else None
        ),
        idempotency_key=idempotency_key,
    )


# ---------------------------------------------------------------------------
# 01 — Event identity / domain
# ---------------------------------------------------------------------------


def test_event_identity_is_tenant_lead_idempotency_scoped():
    tenant_id = uuid4()
    lead_id = uuid4()

    event = LeadDomainEvent.create(
        tenant_id=tenant_id,
        lead_id=lead_id,
        event_type=LeadDomainEventType.LEAD_CREATED,
        correlation_id=uuid4(),
        idempotency_key="event-001",
        payload={"status": "NEW"},
    )

    assert event.identity_key == (
        tenant_id,
        lead_id,
        "event-001",
    )


def test_event_rejects_invalid_event_type():
    with pytest.raises(LeadEventValidationError):
        LeadDomainEvent(
            event_id=uuid4(),
            tenant_id=uuid4(),
            lead_id=uuid4(),
            event_type="NOT_A_REAL_EVENT",
            schema_version=1,
            correlation_id=uuid4(),
            causation_id=None,
            idempotency_key="event-001",
            payload={},
            occurred_at=utc_now(),
        )


def test_event_is_immutable():
    event = LeadDomainEvent.create(
        tenant_id=uuid4(),
        lead_id=uuid4(),
        event_type=LeadDomainEventType.LEAD_CREATED,
        correlation_id=uuid4(),
        idempotency_key="event-immutable",
        payload={"status": "NEW"},
    )

    with pytest.raises(FrozenInstanceError):
        event.idempotency_key = "tampered"


# ---------------------------------------------------------------------------
# 02 — Tenant isolation
# ---------------------------------------------------------------------------


def test_lead_tenant_isolation():
    lead = make_lead()

    with pytest.raises(Exception):
        lead.ensure_tenant(uuid4())


def test_ownership_tenant_isolation():
    lead = make_lead()
    ownership = make_ownership(lead)

    with pytest.raises(OwnershipTenantViolation):
        ownership.ensure_tenant(uuid4())


def test_attribution_tenant_isolation():
    lead = make_lead()

    attribution = LeadAttribution(
        lead_id=lead.lead_id,
        tenant_id=lead.tenant_id,
        source_type="WEBSITE",
        source_reference="source-001",
        attributed_at=utc_now(),
    )

    with pytest.raises(AttributionValidationError):
        attribution.ensure_tenant(uuid4())


def test_event_tenant_isolation():
    tenant_id = uuid4()

    event = LeadDomainEvent.create(
        tenant_id=tenant_id,
        lead_id=uuid4(),
        event_type=LeadDomainEventType.LEAD_CREATED,
        correlation_id=uuid4(),
        idempotency_key="event-tenant",
        payload={},
    )

    with pytest.raises(LeadEventValidationError):
        event.ensure_tenant(uuid4())


def test_acrl_contract_tenant_isolation():
    lead = make_lead()
    precondition = make_precondition(lead, None)

    contract = LeadAcrlIntegrationContract.create(
        tenant_id=lead.tenant_id,
        lead_id=lead.lead_id,
        operation=ReosLeadOperation.UPDATE_LEAD,
        correlation_id=uuid4(),
        idempotency_key="acrl-tenant",
        precondition=precondition,
    )

    foreign_lead = make_lead()

    with pytest.raises(LeadAcrlPreconditionConflict):
        contract.validate_current_domain(
            foreign_lead,
            None,
        )


# ---------------------------------------------------------------------------
# 03 — Serialization / fingerprint
# ---------------------------------------------------------------------------


def test_lead_fingerprint_is_deterministic():
    fixed_time = utc_now()

    lead_a = Lead.create(
        tenant_id=uuid4(),
        customer_id=uuid4(),
        source=LeadSource(
            source_type=LeadSourceType.DIRECT,
        ),
        created_at=fixed_time,
    )

    lead_b = Lead(
        lead_id=lead_a.lead_id,
        tenant_id=lead_a.tenant_id,
        customer_id=lead_a.customer_id,
        status=lead_a.status,
        priority=lead_a.priority,
        source=lead_a.source,
        metadata={"a": 1, "b": 2},
        revision=lead_a.revision,
        created_at=fixed_time,
        updated_at=fixed_time,
    )

    assert (
        lead_a.immutable_fingerprint
        == lead_b.immutable_fingerprint
    )


def test_event_fingerprint_changes_when_payload_changes():
    common = {
        "tenant_id": uuid4(),
        "lead_id": uuid4(),
        "correlation_id": uuid4(),
        "idempotency_key": "event-fingerprint",
    }

    event_a = LeadDomainEvent.create(
        **common,
        event_type=LeadDomainEventType.LEAD_CREATED,
        payload={"status": "NEW"},
    )

    event_b = LeadDomainEvent.create(
        **common,
        event_type=LeadDomainEventType.LEAD_CREATED,
        payload={"status": "QUALIFYING"},
    )

    assert event_a.fingerprint != event_b.fingerprint


def test_event_serialization_is_canonical():
    event = LeadDomainEvent.create(
        tenant_id=uuid4(),
        lead_id=uuid4(),
        event_type=LeadDomainEventType.LEAD_CREATED,
        correlation_id=uuid4(),
        idempotency_key="serialization-001",
        payload={
            "z": 1,
            "a": {
                "y": 2,
                "x": 3,
            },
        },
    )

    first = event.to_core002_payload()
    second = event.to_core002_payload()

    assert first == second
    assert first["fingerprint"] == event.fingerprint


# ---------------------------------------------------------------------------
# 04 — Contract registration / validation
# ---------------------------------------------------------------------------


def test_default_lead_contract_is_available_and_immutable():
    contract = DEFAULT_LEAD_CONTRACT

    assert contract.schema_name == "REOS.CORE-003.LEAD"
    assert contract.schema_version == 1

    with pytest.raises(FrozenInstanceError):
        contract.schema_version = 2


def test_lead_contract_accepts_valid_domain_payload():
    lead = make_lead()

    payload = {
        "lead_id": lead.lead_id,
        "tenant_id": lead.tenant_id,
        "customer_id": lead.customer_id,
        "status": lead.status,
        "priority": lead.priority,
        "source": lead.source,
        "metadata": lead.metadata,
        "revision": lead.revision,
        "created_at": lead.created_at,
        "updated_at": lead.updated_at,
    }

    DEFAULT_LEAD_CONTRACT.validate_mapping(payload)


def test_lead_contract_rejects_missing_required_field():
    lead = make_lead()

    payload = {
        "lead_id": lead.lead_id,
        "tenant_id": lead.tenant_id,
        "customer_id": lead.customer_id,
        "status": lead.status,
        "priority": lead.priority,
        "source": lead.source,
        "metadata": lead.metadata,
        "revision": lead.revision,
        "created_at": lead.created_at,
    }

    with pytest.raises(LeadSchemaError):
        DEFAULT_LEAD_CONTRACT.validate_mapping(payload)


# ---------------------------------------------------------------------------
# 05 — Unknown contract fail-closed
# ---------------------------------------------------------------------------


def test_unknown_lead_field_fails_closed():
    lead = make_lead()

    payload = {
        "lead_id": lead.lead_id,
        "tenant_id": lead.tenant_id,
        "customer_id": lead.customer_id,
        "status": lead.status,
        "priority": lead.priority,
        "source": lead.source,
        "metadata": lead.metadata,
        "revision": lead.revision,
        "created_at": lead.created_at,
        "updated_at": lead.updated_at,
        "unknown_field": "attack",
    }

    with pytest.raises(LeadSchemaError):
        DEFAULT_LEAD_CONTRACT.validate_mapping(payload)


def test_invalid_schema_version_fails_closed():
    with pytest.raises(LeadSchemaError):
        LeadContract(
            schema_version=0,
        )


def test_duplicate_required_fields_fail_closed():
    with pytest.raises(LeadSchemaError):
        LeadContract(
            required_fields=(
                "lead_id",
                "lead_id",
            ),
        )


# ---------------------------------------------------------------------------
# 06 — Ordering stale / future boundary
# ---------------------------------------------------------------------------


def test_stale_lead_revision_is_rejected():
    lead = make_lead()

    precondition = LeadMutationPrecondition(
        tenant_id=lead.tenant_id,
        lead_id=lead.lead_id,
        expected_lead_revision=1,
        expected_ownership_revision=None,
        idempotency_key="stale-operation",
    )

    snapshot = LeadConsistencySnapshot.capture(
        lead,
        None,
    )

    with pytest.raises(LeadConcurrencyConflict):
        precondition.validate_snapshot(snapshot)


def test_future_domain_event_timestamp_is_preserved_without_local_ordering_engine():
    future = utc_now() + timedelta(hours=1)

    event = LeadDomainEvent.create(
        tenant_id=uuid4(),
        lead_id=uuid4(),
        event_type=LeadDomainEventType.LEAD_CREATED,
        correlation_id=uuid4(),
        idempotency_key="future-event",
        payload={},
        occurred_at=future,
    )

    assert event.occurred_at == future.astimezone(
        timezone.utc
    )


# ---------------------------------------------------------------------------
# 07 — Resilience transient / permanent boundary
# ---------------------------------------------------------------------------


def test_invalid_uuid_is_rejected_deterministically():
    with pytest.raises(LeadValidationError):
        Lead.create(
            tenant_id="not-a-uuid",
            customer_id=uuid4(),
            source=LeadSource(
                source_type=LeadSourceType.DIRECT
            ),
        )


def test_unsupported_metadata_type_fails_without_coercion():
    class Unsupported:
        pass

    with pytest.raises(LeadValidationError):
        Lead.create(
            tenant_id=uuid4(),
            customer_id=uuid4(),
            source=LeadSource(
                source_type=LeadSourceType.DIRECT
            ),
            metadata={
                "bad": Unsupported(),
            },
        )


# ---------------------------------------------------------------------------
# 08 — Transport registry boundary
# ---------------------------------------------------------------------------


def test_core_003_event_contract_has_no_transport_registry():
    assert not hasattr(
        LeadDomainEvent,
        "register_transport",
    )

    assert not hasattr(
        LeadDomainEvent,
        "publish",
    )

    assert not hasattr(
        LeadDomainEvent,
        "send",
    )


def test_core_003_event_serialization_is_pure():
    event = LeadDomainEvent.create(
        tenant_id=uuid4(),
        lead_id=uuid4(),
        event_type=LeadDomainEventType.LEAD_CREATED,
        correlation_id=uuid4(),
        idempotency_key="pure-event",
        payload={},
    )

    before = event.fingerprint
    event.to_core002_payload()
    after = event.fingerprint

    assert before == after


# ---------------------------------------------------------------------------
# 09 — Replay authorization / scope
# ---------------------------------------------------------------------------


def test_replay_like_operation_requires_capability():
    context = make_security_context(
        uuid4(),
        {
            LeadCapability.READ_LEAD,
        },
    )

    with pytest.raises(LeadCapabilityViolation):
        context.require(
            LeadCapability.TRANSFER_LEAD
        )


def test_expired_security_context_is_rejected():
    issued = utc_now()

    context = LeadSecurityContext(
        tenant_id=uuid4(),
        actor_id=uuid4(),
        capabilities=frozenset(
            {LeadCapability.READ_LEAD}
        ),
        authorization_reference="auth-expired",
        issued_at=issued,
        expires_at=issued + timedelta(seconds=1),
    )

    with pytest.raises(LeadSecurityContextError):
        context.assert_active(
            now=issued + timedelta(seconds=2)
        )


# ---------------------------------------------------------------------------
# 10 — Replay partial failure
# ---------------------------------------------------------------------------


def test_same_handoff_identity_with_different_payload_fails_closed():
    lead = make_lead()

    first = LeadFraudHandoff.create(
        tenant_id=lead.tenant_id,
        lead_id=lead.lead_id,
        reason=FraudHandoffReason.DUPLICATE_LEAD,
        priority=FraudHandoffPriority.REVIEW,
        idempotency_key="handoff-replay",
        evidence_references=("evidence-001",),
        source_reference="CORE-003",
    )

    conflicting = LeadFraudHandoff.create(
        tenant_id=lead.tenant_id,
        lead_id=lead.lead_id,
        reason=FraudHandoffReason.EVIDENCE_CONFLICT,
        priority=FraudHandoffPriority.HIGH,
        idempotency_key="handoff-replay",
        evidence_references=("evidence-002",),
        source_reference="CORE-003",
    )

    with pytest.raises(FraudHandoffConflictError):
        first.assert_compatible(conflicting)


def test_same_event_identity_with_conflicting_payload_fails_closed():
    tenant_id = uuid4()
    lead_id = uuid4()
    correlation_id = uuid4()

    first = LeadDomainEvent.create(
        tenant_id=tenant_id,
        lead_id=lead_id,
        event_type=LeadDomainEventType.LEAD_CREATED,
        correlation_id=correlation_id,
        idempotency_key="event-replay",
        payload={"status": "NEW"},
    )

    conflicting = LeadDomainEvent.create(
        tenant_id=tenant_id,
        lead_id=lead_id,
        event_type=LeadDomainEventType.LEAD_STATUS_CHANGED,
        correlation_id=correlation_id,
        idempotency_key="event-replay",
        payload={"status": "QUALIFIED"},
    )

    with pytest.raises(LeadEventConflictError):
        first.assert_compatible(conflicting)


# ---------------------------------------------------------------------------
# 11 — Delivery boundary
# ---------------------------------------------------------------------------


def test_core_003_does_not_expose_delivery_operation():
    assert not hasattr(
        LeadDomainEvent,
        "deliver",
    )

    assert not hasattr(
        LeadDomainEvent,
        "retry_delivery",
    )

    assert not hasattr(
        LeadDomainEvent,
        "acknowledge_delivery",
    )


def test_core_002_payload_is_only_a_contract_projection():
    event = LeadDomainEvent.create(
        tenant_id=uuid4(),
        lead_id=uuid4(),
        event_type=LeadDomainEventType.LEAD_CREATED,
        correlation_id=uuid4(),
        idempotency_key="projection-001",
        payload={
            "status": "NEW",
        },
    )

    payload = event.to_core002_payload()

    assert payload["event_id"] == str(
        event.event_id
    )
    assert payload["event_type"] == (
        event.event_type.value
    )
    assert payload["schema_version"] == 1


# ---------------------------------------------------------------------------
# 12 — Transaction / outbox boundary
# ---------------------------------------------------------------------------


def test_core_003_does_not_expose_transaction_engine():
    assert not hasattr(
        LeadDomainEvent,
        "begin_transaction",
    )

    assert not hasattr(
        LeadDomainEvent,
        "commit",
    )

    assert not hasattr(
        LeadDomainEvent,
        "rollback",
    )


def test_core_003_does_not_expose_outbox_engine():
    assert not hasattr(
        LeadDomainEvent,
        "enqueue_outbox",
    )

    assert not hasattr(
        LeadDomainEvent,
        "publish_outbox",
    )


# ---------------------------------------------------------------------------
# 13 — Observability / evidence
# ---------------------------------------------------------------------------


def test_communication_evidence_reference_is_preserved():
    lead = make_lead()

    hook = LeadCommunicationEvidenceHook(
        lead_id=lead.lead_id,
        tenant_id=lead.tenant_id,
        communication_id=uuid4(),
        evidence_reference="communication-evidence-001",
        direction=CommunicationDirection.OUTBOUND,
        channel=CommunicationChannel.EMAIL,
        occurred_at=utc_now(),
    )

    serialized = hook.to_dict()

    assert (
        serialized["evidence_reference"]
        == "communication-evidence-001"
    )
    assert serialized["fingerprint"] == (
        hook.fingerprint
    )


def test_acrl_evidence_references_are_preserved():
    lead = make_lead()

    precondition = make_precondition(
        lead,
        None,
        idempotency_key="evidence-operation",
    )

    contract = LeadAcrlIntegrationContract.create(
        tenant_id=lead.tenant_id,
        lead_id=lead.lead_id,
        operation=(
            ReosLeadOperation.ATTACH_COMMUNICATION_EVIDENCE
        ),
        correlation_id=uuid4(),
        idempotency_key="evidence-operation",
        precondition=precondition,
        evidence_references=(
            "evidence-001",
            "evidence-002",
        ),
    )

    assert contract.evidence_references == (
        "evidence-001",
        "evidence-002",
    )


# ---------------------------------------------------------------------------
# 14 — REOS integration contract
# ---------------------------------------------------------------------------


def test_reos_integration_contract_validates_current_domain():
    lead = make_lead()
    ownership = make_ownership(lead)

    precondition = make_precondition(
        lead,
        ownership,
        idempotency_key="reos-operation",
    )

    contract = LeadAcrlIntegrationContract.create(
        tenant_id=lead.tenant_id,
        lead_id=lead.lead_id,
        operation=ReosLeadOperation.TRANSFER_OWNER,
        correlation_id=uuid4(),
        idempotency_key="reos-operation",
        precondition=precondition,
        expected_post_lead_revision=lead.revision,
        expected_post_ownership_revision=ownership.revision,
    )

    contract.validate_current_domain(
        lead,
        ownership,
    )


# ---------------------------------------------------------------------------
# 15 — ACRL integration contract
# ---------------------------------------------------------------------------


def test_acrl_contract_rejects_stale_domain_revision():
    lead = make_lead()

    precondition = make_precondition(
        lead,
        None,
        idempotency_key="acrl-stale",
    )

    contract = LeadAcrlIntegrationContract.create(
        tenant_id=lead.tenant_id,
        lead_id=lead.lead_id,
        operation=ReosLeadOperation.UPDATE_LEAD,
        correlation_id=uuid4(),
        idempotency_key="acrl-stale",
        precondition=precondition,
    )

    changed = lead.with_priority(
        LeadPriority.HIGH
    )

    with pytest.raises(LeadAcrlPreconditionConflict):
        contract.validate_current_domain(
            changed,
            None,
        )


def test_acrl_contract_fails_closed_on_conflicting_same_operation():
    lead = make_lead()

    precondition = make_precondition(
        lead,
        None,
        idempotency_key="same-operation",
    )

    first = LeadAcrlIntegrationContract.create(
        tenant_id=lead.tenant_id,
        lead_id=lead.lead_id,
        operation=ReosLeadOperation.UPDATE_LEAD,
        correlation_id=uuid4(),
        idempotency_key="same-operation",
        precondition=precondition,
        checkpoint_reference="checkpoint-001",
    )

    second = LeadAcrlIntegrationContract.create(
        tenant_id=lead.tenant_id,
        lead_id=lead.lead_id,
        operation=ReosLeadOperation.UPDATE_LEAD,
        correlation_id=uuid4(),
        idempotency_key="same-operation",
        precondition=precondition,
        checkpoint_reference="checkpoint-002",
    )

    with pytest.raises(LeadAcrlPreconditionConflict):
        first.assert_compatible(second)


# ---------------------------------------------------------------------------
# 16 — Security / producer authorization boundary
# ---------------------------------------------------------------------------


def test_security_context_requires_authorization_reference():
    with pytest.raises(LeadSecurityContextError):
        LeadSecurityContext(
            tenant_id=uuid4(),
            actor_id=uuid4(),
            capabilities=frozenset(
                {LeadCapability.READ_LEAD}
            ),
            authorization_reference="",
            issued_at=utc_now(),
        )


def test_event_producer_cannot_be_blank():
    with pytest.raises(LeadEventValidationError):
        LeadDomainEvent.create(
            tenant_id=uuid4(),
            lead_id=uuid4(),
            event_type=LeadDomainEventType.LEAD_CREATED,
            correlation_id=uuid4(),
            idempotency_key="producer-001",
            payload={},
            producer="",
        )


def test_security_scope_matches_lead_tenant():
    tenant_id = uuid4()

    context = make_security_context(
        tenant_id,
        {LeadCapability.READ_LEAD},
    )

    lead = make_lead(
        tenant_id=tenant_id,
    )

    context.ensure_lead(lead)


# ---------------------------------------------------------------------------
# 17 — Schema evolution / compatibility boundary
# ---------------------------------------------------------------------------


def test_schema_version_change_changes_contract_fingerprint():
    version_one = LeadContract(
        schema_version=1,
    )

    version_two = LeadContract(
        schema_version=2,
    )

    assert (
        version_one.fingerprint
        != version_two.fingerprint
    )


def test_schema_shape_change_changes_contract_fingerprint():
    version_one = LeadContract(
        schema_version=1,
        required_fields=(
            "lead_id",
            "tenant_id",
        ),
    )

    version_changed = LeadContract(
        schema_version=1,
        required_fields=(
            "lead_id",
            "tenant_id",
            "customer_id",
        ),
    )

    assert (
        version_one.fingerprint
        != version_changed.fingerprint
    )


# ---------------------------------------------------------------------------
# 18 — Contract fingerprint immutability
# ---------------------------------------------------------------------------


def test_lead_contract_fingerprint_is_stable():
    fingerprint_a = DEFAULT_LEAD_CONTRACT.fingerprint
    fingerprint_b = DEFAULT_LEAD_CONTRACT.fingerprint

    assert fingerprint_a == fingerprint_b


def test_event_fingerprint_is_stable_without_mutation():
    event = LeadDomainEvent.create(
        tenant_id=uuid4(),
        lead_id=uuid4(),
        event_type=LeadDomainEventType.LEAD_CREATED,
        correlation_id=uuid4(),
        idempotency_key="stable-event",
        payload={
            "status": "NEW",
        },
    )

    first = event.fingerprint
    second = event.fingerprint

    assert first == second


def test_acrl_fingerprint_is_stable():
    lead = make_lead()

    precondition = make_precondition(
        lead,
        None,
        idempotency_key="stable-acrl",
    )

    contract = LeadAcrlIntegrationContract.create(
        tenant_id=lead.tenant_id,
        lead_id=lead.lead_id,
        operation=ReosLeadOperation.UPDATE_LEAD,
        correlation_id=uuid4(),
        idempotency_key="stable-acrl",
        precondition=precondition,
    )

    assert (
        contract.fingerprint
        == contract.fingerprint
    )


# ---------------------------------------------------------------------------
# 19 — Deep adversarial regression
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "bad_priority",
    [
        "HIGH",
        1,
        None,
        object(),
    ],
)
def test_invalid_lead_priority_is_rejected(
    bad_priority,
):
    with pytest.raises(LeadValidationError):
        Lead.create(
            tenant_id=uuid4(),
            customer_id=uuid4(),
            source=LeadSource(
                source_type=LeadSourceType.DIRECT
            ),
            priority=bad_priority,
        )


@pytest.mark.parametrize(
    "bad_timestamp",
    [
        datetime.now(),
        "2026-01-01",
        None,
    ],
)
def test_invalid_lead_timestamp_is_rejected(
    bad_timestamp,
):
    with pytest.raises(LeadValidationError):
        Lead(
            lead_id=uuid4(),
            tenant_id=uuid4(),
            customer_id=uuid4(),
            status=LeadStatus.NEW,
            priority=LeadPriority.NORMAL,
            source=LeadSource(
                source_type=LeadSourceType.DIRECT
            ),
            created_at=bad_timestamp,
            updated_at=bad_timestamp,
        )


def test_ownership_transfer_revision_must_advance_exactly_once():
    lead = make_lead()
    ownership = make_ownership(lead)

    transfer = OwnershipTransfer.create(
        lead_id=lead.lead_id,
        tenant_id=lead.tenant_id,
        previous_owner_id=ownership.owner_id,
        new_owner_id=uuid4(),
        previous_revision=ownership.revision,
        reason=TransferReason.MANUAL,
    )

    assert (
        transfer.new_revision
        == transfer.previous_revision + 1
    )


def test_ownership_transfer_stale_revision_is_rejected():
    lead = make_lead()
    ownership = make_ownership(lead)

    transfer = OwnershipTransfer.create(
        lead_id=lead.lead_id,
        tenant_id=lead.tenant_id,
        previous_owner_id=ownership.owner_id,
        new_owner_id=uuid4(),
        previous_revision=ownership.revision,
        reason=TransferReason.MANUAL,
    )

    with pytest.raises(Exception):
        transfer.ensure_previous_revision(
            ownership.revision + 1
        )


def test_communication_same_identity_conflict_is_detected():
    lead = make_lead()
    communication_id = uuid4()
    timestamp = utc_now()

    first = LeadCommunicationEvidenceHook(
        lead_id=lead.lead_id,
        tenant_id=lead.tenant_id,
        communication_id=communication_id,
        evidence_reference="evidence-a",
        direction=CommunicationDirection.OUTBOUND,
        channel=CommunicationChannel.EMAIL,
        occurred_at=timestamp,
    )

    second = LeadCommunicationEvidenceHook(
        lead_id=lead.lead_id,
        tenant_id=lead.tenant_id,
        communication_id=communication_id,
        evidence_reference="evidence-b",
        direction=CommunicationDirection.OUTBOUND,
        channel=CommunicationChannel.EMAIL,
        occurred_at=timestamp,
    )

    with pytest.raises(
        CommunicationEvidenceConflictError
    ):
        first.assert_compatible(second)
