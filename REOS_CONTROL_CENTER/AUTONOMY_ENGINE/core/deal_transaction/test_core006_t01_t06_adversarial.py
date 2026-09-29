from __future__ import annotations

import pytest

from .deal import Deal, DealStatus
from .deal_acrl_integration import (
    build_acrl_bundle,
    verify_acrl_bundle,
)
from .deal_security import (
    DealAuthorizationContext,
    DealOperation,
    authorize_deal_operation,
)
from .deal_transaction_consistency import (
    validate_deal_consistency,
)
from .deal_transaction_events import (
    DealTransactionEventType,
    transaction_event_from_deal_state,
    transaction_event_from_milestone,
)
from .deal_transaction_milestones import (
    DealTransactionMilestone,
)
from .deal_reos_integration import (
    build_reos_contract,
)


AT = "2026-09-29T06:00:00+00:00"


def make_deal() -> Deal:
    return Deal.create(
        tenant_id="tenant-001",
        customer_id="customer-001",
        broker_id="broker-001",
        builder_id="builder-001",
        project_id="project-001",
        unit_id="unit-001",
        deal_id="deal-001",
        at=AT,
    )


def move_to(
    deal: Deal,
    *states: DealStatus,
) -> Deal:
    current = deal

    for state in states:
        current = current.transition(
            state,
            tenant_id="tenant-001",
            expected_version=current.version,
            at=AT,
        )

    return current


def test_aggregate_version_and_lifecycle_history_are_distinct() -> None:
    deal = make_deal()

    updated = deal.bind_ownership(
        binding_id="binding-001",
        lead_id="lead-001",
        ownership_record_id="ownership-001",
        owner_id="owner-001",
        tenant_id="tenant-001",
        expected_version=deal.version,
        at=AT,
    )

    assert updated.version == 2
    assert len(updated.history) == 1
    assert updated.history[-1].version == 1

    next_deal = updated.transition(
        DealStatus.MATCHED,
        tenant_id="tenant-001",
        expected_version=updated.version,
        at=AT,
    )

    assert next_deal.version == 3
    assert [entry.version for entry in next_deal.history] == [1, 3]


def test_evidence_mutation_does_not_corrupt_lifecycle_history() -> None:
    deal = make_deal()

    updated = deal.attach_evidence(
        tenant_id="tenant-001",
        expected_version=deal.version,
        evidence_type="CUSTOMER_ORIGIN",
        reference="evidence://001",
        evidence_id="evidence-001",
        actor_id="user-001",
        at=AT,
    )

    assert updated.version == 2
    assert len(updated.history) == 1
    assert updated.history[-1].version == 1

    result = validate_deal_consistency(
        updated,
        tenant_id="tenant-001",
    )

    assert result.valid, result.violations


def test_audit_mutation_does_not_corrupt_lifecycle_history() -> None:
    deal = make_deal()

    updated = deal.record_audit(
        tenant_id="tenant-001",
        expected_version=deal.version,
        action="DEAL_CREATED",
        actor_id="user-001",
        audit_id="audit-001",
        at=AT,
    )

    assert updated.version == 2
    assert len(updated.history) == 1
    assert updated.history[-1].version == 1

    result = validate_deal_consistency(
        updated,
        tenant_id="tenant-001",
    )

    assert result.valid, result.violations


def test_ownership_is_reference_only() -> None:
    deal = make_deal()

    updated = deal.bind_ownership(
        binding_id="binding-001",
        lead_id="lead-001",
        ownership_record_id="ownership-001",
        owner_id="owner-001",
        tenant_id="tenant-001",
        expected_version=deal.version,
        at=AT,
    )

    assert updated.ownership_binding is not None
    assert updated.ownership_binding.authority == "ARCH-011"

    payload = updated.ownership_binding.to_dict()

    assert payload["authority"] == "ARCH-011"
    assert "ownership_engine_state" not in payload
    assert "owner_history" not in payload


def test_consistency_rejects_cross_tenant_deal() -> None:
    deal = make_deal()

    result = validate_deal_consistency(
        deal,
        tenant_id="tenant-999",
    )

    assert not result.valid
    assert any(
        violation.code == "TENANT_SCOPE"
        for violation in result.violations
    )


def test_authorization_is_default_deny() -> None:
    deal = make_deal()

    denied = authorize_deal_operation(
        deal,
        DealAuthorizationContext(
            subject_id="user-001",
            tenant_id="tenant-001",
        ),
        DealOperation.TRANSITION,
    )

    assert not denied.allowed
    assert denied.required_permission == "DEAL_TRANSITION"


def test_authorization_respects_tenant_boundary() -> None:
    deal = make_deal()

    denied = authorize_deal_operation(
        deal,
        DealAuthorizationContext(
            subject_id="user-001",
            tenant_id="tenant-999",
            permissions=frozenset(
                {"DEAL_TRANSITION"}
            ),
        ),
        DealOperation.TRANSITION,
    )

    assert not denied.allowed
    assert "Tenant mismatch" in denied.reason


def test_reos_contract_cannot_mutate_control_center_state() -> None:
    deal = make_deal()

    contract = build_reos_contract(deal)

    assert contract.control_center_authoritative is True
    assert contract.state_mutation_authorized is False
    assert contract.source_of_truth == "deal"
    assert "CORE-006-T06" in contract.discoverable_tasks
    assert contract.verification_contract == (
        "REOS_CONTROL_CENTER"
    )


def test_acrl_bundle_is_reconstructable_and_tenant_bound() -> None:
    deal = make_deal()

    bundle = build_acrl_bundle(deal)

    assert bundle.checkpoint_safe is True

    assert verify_acrl_bundle(
        bundle,
        expected_deal_id="deal-001",
        expected_tenant_id="tenant-001",
    )

    assert not verify_acrl_bundle(
        bundle,
        expected_deal_id="deal-001",
        expected_tenant_id="tenant-999",
    )


def test_transaction_event_is_derived_from_milestone() -> None:
    deal = move_to(
        make_deal(),
        DealStatus.MATCHED,
        DealStatus.VISIT_PENDING,
        DealStatus.VISITED,
        DealStatus.OFFERED,
    )

    updated = deal.advance_transaction_milestone(
        DealStatus.BOOKING_PENDING,
        tenant_id="tenant-001",
        expected_version=deal.version,
        reference_id="booking-001",
        at=AT,
    )

    milestone = updated.last_transaction_milestone

    assert milestone is not None

    event = transaction_event_from_milestone(
        milestone
    )

    assert event.event_id == milestone.milestone_id
    assert (
        event.event_type
        is DealTransactionEventType.MILESTONE_COMPLETED
    )
    assert event.deal_id == deal.deal_id
    assert event.tenant_id == deal.tenant_id
    assert event.deal_version == updated.version
    assert event.idempotency_key == event.event_id
    assert event.payload_hash


def test_state_event_is_deterministic() -> None:
    first = transaction_event_from_deal_state(
        deal_id="deal-001",
        tenant_id="tenant-001",
        deal_version=5,
        occurred_at=AT,
        from_status=DealStatus.OFFERED,
        to_status=DealStatus.BOOKING_PENDING,
    )

    second = transaction_event_from_deal_state(
        deal_id="deal-001",
        tenant_id="tenant-001",
        deal_version=5,
        occurred_at=AT,
        from_status=DealStatus.OFFERED,
        to_status=DealStatus.BOOKING_PENDING,
    )

    assert first.event_id == second.event_id
    assert first.idempotency_key == second.idempotency_key
    assert first.to_dict() == second.to_dict()


def test_milestone_scope_is_tenant_and_deal_bound() -> None:
    milestone = DealTransactionMilestone.create(
        deal_id="deal-001",
        tenant_id="tenant-001",
        from_status=DealStatus.OFFERED,
        to_status=DealStatus.BOOKING_PENDING,
        sequence=1,
        deal_version=2,
        occurred_at=AT,
    )

    milestone.assert_scope(
        deal_id="deal-001",
        tenant_id="tenant-001",
    )

    with pytest.raises(Exception):
        milestone.assert_scope(
            deal_id="deal-002",
            tenant_id="tenant-001",
        )

    with pytest.raises(Exception):
        milestone.assert_scope(
            deal_id="deal-001",
            tenant_id="tenant-999",
        )
