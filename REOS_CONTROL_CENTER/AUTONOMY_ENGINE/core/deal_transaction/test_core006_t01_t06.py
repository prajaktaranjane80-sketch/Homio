from __future__ import annotations

import pytest

from .deal import (
    Deal,
    DealStatus,
    DealTenantError,
    DealTransitionError,
)
from .deal_evidence_audit import (
    DealAuditConflictError,
    DealEvidenceConflictError,
)
from .deal_external_contracts import (
    DealExternalAuthority,
    DealExternalReference,
)
from .deal_transaction_milestones import (
    DealTransactionMilestone,
)


AT = "2026-09-29T06:00:00+00:00"


def make_deal(bound: bool = True) -> Deal:
    return Deal.create(
        tenant_id="t1",
        customer_id="c1",
        broker_id="b1",
        builder_id="bu1" if bound else None,
        project_id="p1" if bound else None,
        unit_id="u1" if bound else None,
        deal_id="d1",
        at=AT,
    )


def walk_to(
    current: Deal,
    *states: DealStatus,
) -> Deal:
    for state in states:
        current = current.transition(
            state,
            tenant_id="t1",
            expected_version=current.version,
            at=AT,
        )

    return current


def test_create_and_full_lifecycle() -> None:
    current = walk_to(
        make_deal(),
        DealStatus.MATCHED,
        DealStatus.VISIT_PENDING,
        DealStatus.VISITED,
        DealStatus.OFFERED,
        DealStatus.BOOKING_PENDING,
        DealStatus.BOOKED,
        DealStatus.AGREEMENT_PENDING,
        DealStatus.AGREED,
        DealStatus.REGISTRATION_PENDING,
        DealStatus.REGISTERED,
        DealStatus.COMPLETION_PENDING,
        DealStatus.COMPLETED,
    )

    assert current.status is DealStatus.COMPLETED
    assert len(current.history) == 13


def test_match_requires_bound_inventory_reference() -> None:
    with pytest.raises(DealTransitionError):
        make_deal(False).transition(
            DealStatus.MATCHED,
            tenant_id="t1",
            expected_version=1,
            at=AT,
        )


def test_tenant_and_version_guards() -> None:
    current = make_deal()

    with pytest.raises(DealTenantError):
        current.transition(
            DealStatus.MATCHED,
            tenant_id="wrong",
            expected_version=1,
            at=AT,
        )

    with pytest.raises(Exception):
        current.transition(
            DealStatus.MATCHED,
            tenant_id="t1",
            expected_version=99,
            at=AT,
        )


def test_offer_negotiation_booking_path() -> None:
    current = walk_to(
        make_deal(),
        DealStatus.MATCHED,
        DealStatus.VISIT_PENDING,
        DealStatus.VISITED,
    )

    current = current.create_offer(
        "o1",
        tenant_id="t1",
        expected_version=current.version,
        at=AT,
    )

    current = current.submit_offer(
        "o1",
        tenant_id="t1",
        expected_version=current.version,
        at=AT,
    )

    assert current.status is DealStatus.OFFERED

    current = current.start_negotiation(
        "n1",
        tenant_id="t1",
        expected_version=current.version,
        at=AT,
    )

    current = current.close_negotiation(
        tenant_id="t1",
        expected_version=current.version,
        accepted=True,
        at=AT,
    )

    assert current.status is DealStatus.BOOKING_PENDING


def test_milestone_is_append_only() -> None:
    current = walk_to(
        make_deal(),
        DealStatus.MATCHED,
        DealStatus.VISIT_PENDING,
        DealStatus.VISITED,
        DealStatus.OFFERED,
    )

    updated = current.advance_transaction_milestone(
        DealStatus.BOOKING_PENDING,
        tenant_id="t1",
        expected_version=current.version,
        reference_id="book-1",
        at=AT,
    )

    assert len(updated.milestones) == 1

    milestone = updated.milestones[0]

    assert milestone.from_status == "OFFERED"
    assert milestone.to_status == "BOOKING_PENDING"
    assert milestone.deal_version == updated.version

    second = updated.advance_transaction_milestone(
        DealStatus.BOOKED,
        tenant_id="t1",
        expected_version=updated.version,
        reference_id="book-2",
        at=AT,
    )

    assert len(second.milestones) == 2
    assert second.milestones[0] == updated.milestones[0]


def test_milestone_is_immutable() -> None:
    milestone = DealTransactionMilestone.create(
        deal_id="d1",
        tenant_id="t1",
        from_status="OFFERED",
        to_status="BOOKING_PENDING",
        sequence=1,
        deal_version=5,
        occurred_at=AT,
    )

    with pytest.raises(AttributeError):
        milestone.sequence = 2  # type: ignore[misc]


def test_ownership_is_external_authority_reference() -> None:
    current = make_deal()

    updated = current.bind_ownership(
        binding_id="bind-1",
        lead_id="lead-1",
        ownership_record_id="own-1",
        owner_id="owner-1",
        tenant_id="t1",
        expected_version=current.version,
        at=AT,
    )

    assert updated.ownership_binding is not None
    assert updated.ownership_binding.authority == "ARCH-011"


def test_evidence_is_idempotent_and_conflict_safe() -> None:
    current = make_deal()

    updated = current.attach_evidence(
        "e1",
        evidence_type="ORIGIN",
        reference="ref://1",
        tenant_id="t1",
        expected_version=current.version,
        at=AT,
    )

    assert updated.version == 2

    same = updated.attach_evidence(
        "e1",
        evidence_type="ORIGIN",
        reference="ref://1",
        tenant_id="t1",
        expected_version=updated.version,
        at=AT,
    )

    assert same is updated

    with pytest.raises(DealEvidenceConflictError):
        updated.attach_evidence(
            "e1",
            evidence_type="ORIGIN",
            reference="ref://changed",
            tenant_id="t1",
            expected_version=updated.version,
            at=AT,
        )


def test_audit_is_idempotent_and_conflict_safe() -> None:
    current = make_deal()

    updated = current.record_audit(
        audit_id="a1",
        action="CREATED",
        actor_id="u1",
        tenant_id="t1",
        expected_version=current.version,
        at=AT,
    )

    assert updated.version == 2

    same = updated.record_audit(
        audit_id="a1",
        action="CREATED",
        actor_id="u1",
        tenant_id="t1",
        expected_version=updated.version,
        at=AT,
    )

    assert same is updated

    with pytest.raises(DealAuditConflictError):
        updated.record_audit(
            audit_id="a1",
            action="CHANGED",
            actor_id="u1",
            tenant_id="t1",
            expected_version=updated.version,
            at=AT,
        )


def test_external_contract_is_scope_bound() -> None:
    reference = DealExternalReference(
        deal_id="d1",
        tenant_id="t1",
        authority=DealExternalAuthority.INVENTORY,
        reference_id="unit-1",
        reference_type="INVENTORY_UNIT",
        authority_version="1",
        created_at=AT,
    )

    reference.assert_scope(
        deal_id="d1",
        tenant_id="t1",
    )

    with pytest.raises(Exception):
        reference.assert_scope(
            deal_id="d2",
            tenant_id="t1",
        )


def test_serialization_is_canonical() -> None:
    current = make_deal()

    payload = current.to_dict()

    assert payload["source_of_truth"] == "deal"
    assert payload["status"] == "QUALIFIED"
    assert payload["history"][0]["reason"] == "DEAL_CREATED"
