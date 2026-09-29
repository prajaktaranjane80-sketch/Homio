from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
from uuid import uuid4

import pytest

from .deal_evidence_audit import (
    DealAuditEntry,
    DealEvidenceReference,
)
from .deal_offer_negotiation import (
    DealNegotiation,
    DealNegotiationStatus,
    DealOffer,
    DealOfferStatus,
)
from .deal_ownership_integration import (
    DealOwnershipBinding,
)
from .deal_transaction_events import (
    CORE002_EVENT_VERSION,
    CORE002_SCHEMA_NAME,
    CORE002_SCHEMA_VERSION,
    DealTransactionEvent,
    DealTransactionEventConflictError,
    DealTransactionEventScopeError,
    DealTransactionEventType,
    build_core002_event_contracts,
    transaction_event_from_audit,
    transaction_event_from_deal_created,
    transaction_event_from_deal_state,
    transaction_event_from_evidence,
    transaction_event_from_milestone,
    transaction_event_from_negotiation_state,
    transaction_event_from_offer_created,
    transaction_event_from_offer_state,
    transaction_event_from_ownership,
)
from .deal_transaction_milestones import (
    DealTransactionMilestone,
)
from .deal_contract import (
    DealStatus,
)

from ..event_platform import (
    EventContractRegistry,
    EventEnvelope,
)


def _tenant() -> str:
    return str(uuid4())


def _deal_id() -> str:
    return str(uuid4())


def _time() -> str:
    return datetime.now(timezone.utc).isoformat()


def test_t07_event_types_cover_required_transaction_workflows() -> None:
    expected = {
        "DEAL_CREATED",
        "DEAL_STATE_CHANGED",
        "OFFER_CREATED",
        "OFFER_STATE_CHANGED",
        "NEGOTIATION_STATE_CHANGED",
        "BOOKING_STATE_CHANGED",
        "MILESTONE_COMPLETED",
        "OWNERSHIP_REFERENCE_CHANGED",
        "EVIDENCE_ATTACHED",
        "AUDIT_RECORDED",
    }

    assert {
        item.value
        for item in DealTransactionEventType
    } == expected


def test_t07_deal_created_event_is_deterministic() -> None:
    event = transaction_event_from_deal_created(
        deal_id="deal-001",
        tenant_id="tenant-001",
        deal_version=1,
        occurred_at=_time(),
    )

    assert event.event_type is DealTransactionEventType.DEAL_CREATED
    assert event.deal_id == "deal-001"
    assert event.tenant_id == "tenant-001"
    assert event.deal_version == 1
    assert event.event_id == event.idempotency_key
    assert event.payload_hash


def test_t07_deal_state_event_maps_transaction_state() -> None:
    event = transaction_event_from_deal_state(
        deal_id="deal-001",
        tenant_id="tenant-001",
        deal_version=7,
        occurred_at=_time(),
        from_status=DealStatus.OFFERED,
        to_status=DealStatus.BOOKING_PENDING,
    )

    assert (
        event.event_type
        is DealTransactionEventType.BOOKING_STATE_CHANGED
    )

    assert event.payload["from_status"] == "OFFERED"
    assert event.payload["to_status"] == "BOOKING_PENDING"
    assert event.deal_version == 7


def test_t07_offer_created_and_state_events() -> None:
    offer = DealOffer.create(
        offer_id="offer-001",
        deal_id="deal-001",
        tenant_id="tenant-001",
    )

    created = transaction_event_from_offer_created(
        offer,
    )

    updated = offer.transition(
        DealOfferStatus.SUBMITTED,
        tenant_id="tenant-001",
        expected_version=1,
    )

    changed = transaction_event_from_offer_state(
        offer=updated,
        from_status=DealOfferStatus.DRAFT,
        to_status=DealOfferStatus.SUBMITTED,
        deal_version=3,
        occurred_at=updated.updated_at,
    )

    assert created.event_type is DealTransactionEventType.OFFER_CREATED
    assert changed.event_type is DealTransactionEventType.OFFER_STATE_CHANGED
    assert changed.payload["offer_id"] == "offer-001"
    assert changed.payload["from_status"] == "DRAFT"
    assert changed.payload["to_status"] == "SUBMITTED"
    assert changed.payload["offer_version"] == 2


def test_t07_negotiation_event() -> None:
    negotiation = DealNegotiation.create(
        negotiation_id="neg-001",
        deal_id="deal-001",
        tenant_id="tenant-001",
        active_offer_id="offer-001",
    )

    event = transaction_event_from_negotiation_state(
        negotiation=negotiation,
        from_status=DealNegotiationStatus.OPEN,
        to_status=DealNegotiationStatus.AGREED,
        deal_version=9,
        occurred_at=negotiation.updated_at,
    )

    assert (
        event.event_type
        is DealTransactionEventType.NEGOTIATION_STATE_CHANGED
    )

    assert event.payload["negotiation_id"] == "neg-001"
    assert event.payload["from_status"] == "OPEN"
    assert event.payload["to_status"] == "AGREED"
    assert event.deal_version == 9


def test_t07_milestone_event() -> None:
    milestone = DealTransactionMilestone.create(
        deal_id="deal-001",
        tenant_id="tenant-001",
        from_status=DealStatus.BOOKING_PENDING,
        to_status=DealStatus.BOOKED,
        sequence=1,
        deal_version=10,
        reference_id="booking-001",
    )

    event = transaction_event_from_milestone(
        milestone,
    )

    assert (
        event.event_type
        is DealTransactionEventType.MILESTONE_COMPLETED
    )

    assert event.payload["milestone_id"] == milestone.milestone_id
    assert event.payload["to_status"] == "BOOKED"
    assert event.payload["sequence"] == 1


def test_t07_ownership_event() -> None:
    binding = DealOwnershipBinding(
        binding_id="binding-001",
        deal_id="deal-001",
        tenant_id="tenant-001",
        lead_id="lead-001",
        ownership_record_id="ownership-001",
        owner_id="owner-001",
        bound_at=datetime.now(timezone.utc),
    )

    event = transaction_event_from_ownership(
        binding,
        deal_version=11,
        occurred_at=_time(),
    )

    assert (
        event.event_type
        is DealTransactionEventType.OWNERSHIP_REFERENCE_CHANGED
    )

    assert event.payload["binding"]["binding_id"] == "binding-001"
    assert event.payload["binding"]["authority"] == "ARCH-011"


def test_t07_evidence_event() -> None:
    evidence = DealEvidenceReference.create(
        evidence_id="evidence-001",
        deal_id="deal-001",
        tenant_id="tenant-001",
        evidence_type="VISIT_PROOF",
        reference="ref://visit/001",
        deal_version=12,
    )

    event = transaction_event_from_evidence(
        evidence,
        deal_version=12,
    )

    assert (
        event.event_type
        is DealTransactionEventType.EVIDENCE_ATTACHED
    )

    assert event.payload["evidence"]["evidence_id"] == "evidence-001"
    assert event.payload["evidence"]["source_of_truth"] == "ARCH-014"


def test_t07_audit_event() -> None:
    audit = DealAuditEntry.create(
        audit_id="audit-001",
        deal_id="deal-001",
        tenant_id="tenant-001",
        action="BOOKING_APPROVED",
        actor_id="actor-001",
        deal_version=13,
    )

    event = transaction_event_from_audit(
        audit,
    )

    assert (
        event.event_type
        is DealTransactionEventType.AUDIT_RECORDED
    )

    assert event.payload["audit"]["audit_id"] == "audit-001"
    assert event.payload["audit"]["action"] == "BOOKING_APPROVED"


def test_t07_event_is_core002_compatible() -> None:
    tenant_uuid = uuid4()

    event = transaction_event_from_deal_created(
        deal_id="deal-001",
        tenant_id=str(tenant_uuid),
        deal_version=1,
        occurred_at=_time(),
    )

    contracts = build_core002_event_contracts()

    assert len(contracts) == len(DealTransactionEventType)

    registry = EventContractRegistry()

    for contract in contracts:
        registry.register(contract)

    payload = event.to_core002_payload()

    envelope = EventEnvelope.create(
        event_type=event.event_type.value,
        schema_name=CORE002_SCHEMA_NAME,
        schema_version=CORE002_SCHEMA_VERSION,
        event_version=CORE002_EVENT_VERSION,
        tenant_id=tenant_uuid,
        producer_id=uuid4(),
        payload=payload,
        correlation_id=uuid4(),
        idempotency_key=event.idempotency_key,
    )

    registry.validate(envelope)

    assert payload["schema_name"] == CORE002_SCHEMA_NAME
    assert payload["schema_version"] == CORE002_SCHEMA_VERSION
    assert payload["event_version"] == CORE002_EVENT_VERSION
    assert payload["deal_id"] == "deal-001"
    assert payload["idempotency_key"] == event.idempotency_key


def test_t07_core002_contracts_cover_every_event_type() -> None:
    contracts = build_core002_event_contracts()

    keys = {
        contract.event_type
        for contract in contracts
    }

    assert keys == {
        event_type.value
        for event_type in DealTransactionEventType
    }


def test_t07_event_identity_is_idempotent() -> None:
    event = transaction_event_from_deal_created(
        deal_id="deal-001",
        tenant_id="tenant-001",
        deal_version=1,
        occurred_at="2026-01-01T00:00:00+00:00",
    )

    duplicate = replace(event)

    event.assert_compatible(duplicate)


def test_t07_conflicting_same_identity_is_rejected() -> None:
    event = transaction_event_from_deal_created(
        deal_id="deal-001",
        tenant_id="tenant-001",
        deal_version=1,
        occurred_at="2026-01-01T00:00:00+00:00",
    )

    conflict = replace(
        event,
        payload={"metadata": {"changed": True}},
    )

    with pytest.raises(
        DealTransactionEventConflictError,
    ):
        event.assert_compatible(conflict)


def test_t07_tenant_scope_is_enforced() -> None:
    event = transaction_event_from_deal_created(
        deal_id="deal-001",
        tenant_id="tenant-001",
        deal_version=1,
        occurred_at=_time(),
    )

    with pytest.raises(
        DealTransactionEventScopeError,
    ):
        event.assert_scope(
            deal_id="deal-001",
            tenant_id="tenant-999",
        )


def test_t07_payload_is_immutable() -> None:
    event = transaction_event_from_deal_created(
        deal_id="deal-001",
        tenant_id="tenant-001",
        deal_version=1,
        occurred_at=_time(),
    )

    with pytest.raises(TypeError):
        event.payload["new"] = "value"  # type: ignore[index]


def test_t07_event_serialization_contains_integrity_fields() -> None:
    event = transaction_event_from_deal_created(
        deal_id="deal-001",
        tenant_id="tenant-001",
        deal_version=1,
        occurred_at=_time(),
    )

    payload = event.to_dict()

    assert payload["event_id"]
    assert payload["event_type"]
    assert payload["schema_version"] == "1.0"
    assert payload["source_of_truth"] == "deal"
    assert payload["payload_hash"]
    assert payload["idempotency_key"] == payload["event_id"]


def test_t07_event_does_not_own_transport_or_bus() -> None:
    event = transaction_event_from_deal_created(
        deal_id="deal-001",
        tenant_id="tenant-001",
        deal_version=1,
        occurred_at=_time(),
    )

    serialized = str(event.to_dict()).lower()

    assert "kafka" not in serialized
    assert "eventbus" not in serialized
    assert "outbox" not in serialized
    assert "transport" not in serialized