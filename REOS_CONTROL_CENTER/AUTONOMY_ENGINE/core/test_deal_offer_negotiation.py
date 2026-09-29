from __future__ import annotations

from datetime import datetime, timezone

import pytest

from AUTONOMY_ENGINE.core.deal import (
    Deal,
    DealOfferStatus,
    DealNegotiationStatus,
    DealReferenceConflictError,
    DealTransitionError,
)


AT = datetime(2026, 9, 23, 10, 0, tzinfo=timezone.utc)


@pytest.fixture
def visited_deal() -> Deal:
    deal = Deal.create(
        tenant_id="tenant-001",
        customer_id="customer-001",
        broker_id="broker-001",
        at=AT,
    )
    return deal.bind_opportunity(
        builder_id="builder-001",
        project_id="project-001",
        unit_id="unit-001",
        tenant_id="tenant-001",
        expected_version=deal.version,
        at=AT,
    ).transition(
        __import__(
            "AUTONOMY_ENGINE.core.deal",
            fromlist=["DealStatus"],
        ).DealStatus.MATCHED,
        tenant_id="tenant-001",
        expected_version=2,
        at=AT,
    ).transition(
        __import__(
            "AUTONOMY_ENGINE.core.deal",
            fromlist=["DealStatus"],
        ).DealStatus.VISIT_PENDING,
        tenant_id="tenant-001",
        expected_version=3,
        at=AT,
    ).transition(
        __import__(
            "AUTONOMY_ENGINE.core.deal",
            fromlist=["DealStatus"],
        ).DealStatus.VISITED,
        tenant_id="tenant-001",
        expected_version=4,
        at=AT,
    )


def test_create_offer_is_draft_and_versioned(visited_deal: Deal):
    updated = visited_deal.create_offer(
        "offer-001",
        tenant_id="tenant-001",
        expected_version=5,
        at=AT,
    )

    assert updated.current_offer is not None
    assert updated.current_offer.status is DealOfferStatus.DRAFT
    assert updated.current_offer.offer_id == "offer-001"
    assert updated.version == 6
    assert updated.status.value == "VISITED"


def test_submit_offer_moves_deal_to_offered(visited_deal: Deal):
    created = visited_deal.create_offer(
        "offer-001",
        tenant_id="tenant-001",
        expected_version=5,
        at=AT,
    )

    updated = created.submit_offer(
        "offer-001",
        tenant_id="tenant-001",
        expected_version=6,
        at=AT,
    )

    assert updated.status.value == "OFFERED"
    assert updated.current_offer.status is DealOfferStatus.SUBMITTED
    assert updated.version == 7
    assert updated.history[-1].reason == "OFFER_SUBMITTED"


def test_duplicate_offer_id_is_idempotent(visited_deal: Deal):
    updated = visited_deal.create_offer(
        "offer-001",
        tenant_id="tenant-001",
        expected_version=5,
        at=AT,
    )

    again = updated.create_offer(
        "offer-001",
        tenant_id="tenant-001",
        expected_version=updated.version,
        at=AT,
    )

    assert again is updated


def test_superseding_offer_requires_existing_offer(visited_deal: Deal):
    with pytest.raises(DealReferenceConflictError):
        visited_deal.create_offer(
            "offer-002",
            tenant_id="tenant-001",
            expected_version=5,
            supersedes_offer_id="missing",
            at=AT,
        )


def test_negotiation_requires_submitted_offer(visited_deal: Deal):
    created = visited_deal.create_offer(
        "offer-001",
        tenant_id="tenant-001",
        expected_version=5,
        at=AT,
    )

    with pytest.raises(DealTransitionError):
        created.start_negotiation(
            "neg-001",
            tenant_id="tenant-001",
            expected_version=6,
            at=AT,
        )


def test_start_negotiation_is_explicit(visited_deal: Deal):
    created = visited_deal.create_offer(
        "offer-001",
        tenant_id="tenant-001",
        expected_version=5,
        at=AT,
    )

    offered = created.submit_offer(
        "offer-001",
        tenant_id="tenant-001",
        expected_version=6,
        at=AT,
    )

    negotiating = offered.start_negotiation(
        "neg-001",
        tenant_id="tenant-001",
        expected_version=7,
        at=AT,
    )

    assert negotiating.status.value == "NEGOTIATING"
    assert negotiating.negotiation is not None
    assert negotiating.negotiation.status is DealNegotiationStatus.OPEN
    assert negotiating.negotiation.active_offer_id == "offer-001"
    assert negotiating.negotiation.round_number == 1
    assert negotiating.history[-1].reason == "NEGOTIATION_STARTED"


def test_pause_and_resume_negotiation(visited_deal: Deal):
    current = visited_deal.create_offer(
        "offer-001",
        tenant_id="tenant-001",
        expected_version=5,
        at=AT,
    ).submit_offer(
        "offer-001",
        tenant_id="tenant-001",
        expected_version=6,
        at=AT,
    ).start_negotiation(
        "neg-001",
        tenant_id="tenant-001",
        expected_version=7,
        at=AT,
    )

    paused = current.transition_negotiation(
        DealNegotiationStatus.PAUSED,
        tenant_id="tenant-001",
        expected_version=8,
        at=AT,
    )

    resumed = paused.transition_negotiation(
        DealNegotiationStatus.OPEN,
        tenant_id="tenant-001",
        expected_version=9,
        at=AT,
    )

    assert resumed.status.value == "NEGOTIATING"
    assert resumed.negotiation.status is DealNegotiationStatus.OPEN


def test_negotiation_round_is_versioned(visited_deal: Deal):
    current = visited_deal.create_offer(
        "offer-001",
        tenant_id="tenant-001",
        expected_version=5,
        at=AT,
    ).submit_offer(
        "offer-001",
        tenant_id="tenant-001",
        expected_version=6,
        at=AT,
    ).start_negotiation(
        "neg-001",
        tenant_id="tenant-001",
        expected_version=7,
        at=AT,
    ).advance_negotiation_round(
        tenant_id="tenant-001",
        expected_version=8,
        active_offer_id="offer-001",
        at=AT,
    )

    assert current.negotiation.round_number == 2
    assert current.negotiation.version == 2


def test_concluded_negotiation_returns_deal_to_offered(visited_deal: Deal):
    current = visited_deal.create_offer(
        "offer-001",
        tenant_id="tenant-001",
        expected_version=5,
        at=AT,
    ).submit_offer(
        "offer-001",
        tenant_id="tenant-001",
        expected_version=6,
        at=AT,
    ).start_negotiation(
        "neg-001",
        tenant_id="tenant-001",
        expected_version=7,
        at=AT,
    )

    concluded = current.transition_negotiation(
        DealNegotiationStatus.CONCLUDED,
        tenant_id="tenant-001",
        expected_version=8,
        at=AT,
    )

    assert concluded.status.value == "OFFERED"
    assert concluded.negotiation.status is DealNegotiationStatus.CONCLUDED
    assert concluded.history[-1].reason == "NEGOTIATION_CONCLUDED"


def test_aborted_negotiation_returns_deal_to_offered(visited_deal: Deal):
    current = visited_deal.create_offer(
        "offer-001",
        tenant_id="tenant-001",
        expected_version=5,
        at=AT,
    ).submit_offer(
        "offer-001",
        tenant_id="tenant-001",
        expected_version=6,
        at=AT,
    ).start_negotiation(
        "neg-001",
        tenant_id="tenant-001",
        expected_version=7,
        at=AT,
    )

    aborted = current.transition_negotiation(
        DealNegotiationStatus.ABORTED,
        tenant_id="tenant-001",
        expected_version=8,
        at=AT,
    )

    assert aborted.status.value == "OFFERED"
    assert aborted.negotiation.status is DealNegotiationStatus.ABORTED


def test_offer_and_negotiation_are_tenant_safe(visited_deal: Deal):
    created = visited_deal.create_offer(
        "offer-001",
        tenant_id="tenant-001",
        expected_version=5,
        at=AT,
    )

    with pytest.raises(Exception):
        created.submit_offer(
            "offer-001",
            tenant_id="tenant-002",
            expected_version=6,
            at=AT,
        )


def test_offer_stale_version_is_blocked(visited_deal: Deal):
    created = visited_deal.create_offer(
        "offer-001",
        tenant_id="tenant-001",
        expected_version=5,
        at=AT,
    )

    with pytest.raises(Exception):
        created.submit_offer(
            "offer-001",
            tenant_id="tenant-001",
            expected_version=999,
            at=AT,
        )


def test_closed_negotiation_cannot_resume(visited_deal: Deal):
    current = visited_deal.create_offer(
        "offer-001",
        tenant_id="tenant-001",
        expected_version=5,
        at=AT,
    ).submit_offer(
        "offer-001",
        tenant_id="tenant-001",
        expected_version=6,
        at=AT,
    ).start_negotiation(
        "neg-001",
        tenant_id="tenant-001",
        expected_version=7,
        at=AT,
    ).transition_negotiation(
        DealNegotiationStatus.CONCLUDED,
        tenant_id="tenant-001",
        expected_version=8,
        at=AT,
    )

    with pytest.raises(Exception):
        current.transition_negotiation(
            DealNegotiationStatus.OPEN,
            tenant_id="tenant-001",
            expected_version=9,
            at=AT,
        )


def test_terminal_deal_cannot_create_offer():
    DealStatus = __import__(
        "AUTONOMY_ENGINE.core.deal",
        fromlist=["DealStatus"],
    ).DealStatus

    deal = Deal.create(
        tenant_id="tenant-001",
        customer_id="customer-001",
        broker_id="broker-001",
        builder_id="builder-001",
        project_id="project-001",
        unit_id="unit-001",
        at=AT,
    )

    current = deal
    previous = current.version

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
        previous += 1

    with pytest.raises(DealReferenceConflictError):
        current.create_offer(
            "offer-terminal",
            tenant_id="tenant-001",
            expected_version=current.version,
            at=AT,
        )


def test_serialization_contains_offer_and_negotiation_state(visited_deal: Deal):
    current = visited_deal.create_offer(
        "offer-001",
        tenant_id="tenant-001",
        expected_version=5,
        at=AT,
    ).submit_offer(
        "offer-001",
        tenant_id="tenant-001",
        expected_version=6,
        at=AT,
    ).start_negotiation(
        "neg-001",
        tenant_id="tenant-001",
        expected_version=7,
        at=AT,
    )

    payload = current.to_dict()

    assert payload["offers"][0]["offer_id"] == "offer-001"
    assert payload["offers"][0]["status"] == "SUBMITTED"
    assert payload["negotiation"]["negotiation_id"] == "neg-001"
    assert payload["negotiation"]["status"] == "OPEN"


def test_offer_history_can_reference_superseded_offer(visited_deal: Deal):
    first = visited_deal.create_offer(
        "offer-001",
        tenant_id="tenant-001",
        expected_version=5,
        at=AT,
    )

    second = first.create_offer(
        "offer-002",
        tenant_id="tenant-001",
        expected_version=6,
        supersedes_offer_id="offer-001",
        at=AT,
    )

    assert second.offers[-1].supersedes_offer_id == "offer-001"
    assert len(second.offers) == 2
