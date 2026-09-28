from __future__ import annotations

import pytest

from AUTONOMY_ENGINE.core.deal import Deal, DealStatus, DealTransitionError
from AUTONOMY_ENGINE.core.deal_transaction_milestones import (
    DealTransactionMilestone,
    DealMilestoneTransitionError,
)


AT = "2026-09-23T10:00:00+00:00"


def base_deal() -> Deal:
    deal = Deal.create(
        tenant_id="tenant-001",
        customer_id="customer-001",
        broker_id="broker-001",
        at=AT,
    )

    deal = deal.bind_opportunity(
        builder_id="builder-001",
        project_id="project-001",
        unit_id="unit-001",
        tenant_id="tenant-001",
        expected_version=deal.version,
        at=AT,
    )

    current = deal

    for target in (
        DealStatus.MATCHED,
        DealStatus.VISIT_PENDING,
        DealStatus.VISITED,
        DealStatus.OFFERED,
    ):
        current = current.transition(
            target,
            tenant_id="tenant-001",
            expected_version=current.version,
            at=AT,
        )

    return current


def test_booking_pending_creates_milestone():
    deal = base_deal()

    updated = deal.advance_transaction_milestone(
        DealStatus.BOOKING_PENDING,
        tenant_id="tenant-001",
        expected_version=deal.version,
        reference_id="booking-request-001",
        at=AT,
    )

    assert updated.status is DealStatus.BOOKING_PENDING
    assert len(updated.milestones) == 1

    milestone = updated.last_transaction_milestone
    assert milestone.to_status is DealStatus.BOOKING_PENDING
    assert milestone.from_status is DealStatus.OFFERED
    assert milestone.sequence == 1
    assert milestone.deal_version == updated.version
    assert milestone.reference_id == "booking-request-001"


def test_full_transaction_milestone_chain_is_monotonic():
    current = base_deal()

    targets = (
        DealStatus.BOOKING_PENDING,
        DealStatus.BOOKED,
        DealStatus.AGREEMENT_PENDING,
        DealStatus.AGREED,
        DealStatus.REGISTRATION_PENDING,
        DealStatus.REGISTERED,
        DealStatus.COMPLETION_PENDING,
        DealStatus.COMPLETED,
    )

    expected_version = current.version

    for target in targets:
        current = current.advance_transaction_milestone(
            target,
            tenant_id="tenant-001",
            expected_version=expected_version,
            reference_id=f"REF-{target.value}",
            at=AT,
        )
        expected_version = current.version

    assert current.status is DealStatus.COMPLETED
    assert len(current.milestones) == 8
    assert [x.sequence for x in current.milestones] == list(range(1, 9))


def test_milestone_versions_match_deal_versions():
    current = base_deal()

    versions = []

    for target in (
        DealStatus.BOOKING_PENDING,
        DealStatus.BOOKED,
        DealStatus.AGREEMENT_PENDING,
    ):
        current = current.advance_transaction_milestone(
            target,
            tenant_id="tenant-001",
            expected_version=current.version,
            at=AT,
        )
        versions.append(current.milestones[-1].deal_version)

    assert versions == [
        current.milestones[0].deal_version,
        current.milestones[1].deal_version,
        current.milestones[2].deal_version,
    ]
    assert versions == sorted(versions)


def test_non_transaction_status_is_rejected():
    deal = base_deal()

    with pytest.raises(DealTransitionError):
        deal.advance_transaction_milestone(
            DealStatus.MATCHED,
            tenant_id="tenant-001",
            expected_version=deal.version,
            at=AT,
        )


def test_invalid_sequence_is_rejected_by_canonical_deal_transition():
    deal = base_deal()

    with pytest.raises(Exception):
        deal.advance_transaction_milestone(
            DealStatus.BOOKED,
            tenant_id="tenant-001",
            expected_version=deal.version,
            at=AT,
        )


def test_cross_tenant_milestone_is_blocked():
    deal = base_deal()

    with pytest.raises(Exception):
        deal.advance_transaction_milestone(
            DealStatus.BOOKING_PENDING,
            tenant_id="tenant-002",
            expected_version=deal.version,
            at=AT,
        )


def test_stale_version_is_blocked():
    deal = base_deal()

    with pytest.raises(Exception):
        deal.advance_transaction_milestone(
            DealStatus.BOOKING_PENDING,
            tenant_id="tenant-001",
            expected_version=999,
            at=AT,
        )


def test_milestone_is_immutable():
    deal = base_deal()

    updated = deal.advance_transaction_milestone(
        DealStatus.BOOKING_PENDING,
        tenant_id="tenant-001",
        expected_version=deal.version,
        at=AT,
    )

    milestone = updated.milestones[0]

    with pytest.raises(Exception):
        milestone.sequence = 99


def test_milestone_serialization_preserves_audit_fields():
    deal = base_deal()

    updated = deal.advance_transaction_milestone(
        DealStatus.BOOKING_PENDING,
        tenant_id="tenant-001",
        expected_version=deal.version,
        reference_id="BOOK-001",
        at=AT,
    )

    payload = updated.to_dict()

    assert len(payload["milestones"]) == 1
    assert payload["milestones"][0]["deal_id"] == deal.deal_id
    assert payload["milestones"][0]["tenant_id"] == "tenant-001"
    assert payload["milestones"][0]["from_status"] == "OFFERED"
    assert payload["milestones"][0]["to_status"] == "BOOKING_PENDING"
    assert payload["milestones"][0]["reference_id"] == "BOOK-001"


def test_milestone_object_serialization_is_stable():
    milestone = DealTransactionMilestone(
        milestone_id="m-001",
        deal_id="deal-001",
        tenant_id="tenant-001",
        from_status=DealStatus.OFFERED,
        to_status=DealStatus.BOOKING_PENDING,
        sequence=1,
        deal_version=6,
        occurred_at=__import__(
            "datetime"
        ).datetime.fromisoformat(AT),
        reference_id="BOOK-001",
    )

    data = milestone.to_dict()

    assert data["milestone_id"] == "m-001"
    assert data["from_status"] == "OFFERED"
    assert data["to_status"] == "BOOKING_PENDING"
    assert data["sequence"] == 1
    assert data["deal_version"] == 6
    assert data["reference_id"] == "BOOK-001"


def test_terminal_deal_cannot_advance_milestone():
    current = Deal.create(
        tenant_id="tenant-001",
        customer_id="customer-001",
        broker_id="broker-001",
        builder_id="builder-001",
        project_id="project-001",
        unit_id="unit-001",
        at=AT,
    )

    for target in (
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
    ):
        current = current.transition(
            target,
            tenant_id="tenant-001",
            expected_version=current.version,
            at=AT,
        )

    with pytest.raises(Exception):
        current.advance_transaction_milestone(
            DealStatus.BOOKING_PENDING,
            tenant_id="tenant-001",
            expected_version=current.version,
            at=AT,
        )


def test_milestones_are_append_only():
    current = base_deal()

    first = current.advance_transaction_milestone(
        DealStatus.BOOKING_PENDING,
        tenant_id="tenant-001",
        expected_version=current.version,
        at=AT,
    )

    second = first.advance_transaction_milestone(
        DealStatus.BOOKED,
        tenant_id="tenant-001",
        expected_version=first.version,
        at=AT,
    )

    assert len(first.milestones) == 1
    assert len(second.milestones) == 2
    assert second.milestones[0] == first.milestones[0]


