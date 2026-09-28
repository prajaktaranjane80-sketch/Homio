from __future__ import annotations

from datetime import datetime, timezone

import pytest

from AUTONOMY_ENGINE.core.deal import (
    Deal,
    DealConcurrencyError,
    DealReferenceConflictError,
    DealStatus,
    DealTenantError,
    DealTransitionError,
    DealValidationError,
)


AT = "2026-09-23T10:00:00+00:00"


def create_deal(*, bound: bool = False) -> Deal:
    return Deal.create(
        tenant_id="tenant-001",
        customer_id="customer-001",
        broker_id="broker-001",
        builder_id="builder-001" if bound else None,
        project_id="project-001" if bound else None,
        unit_id="unit-001" if bound else None,
        deal_id="deal-001",
        at=AT,
    )


def bound_deal() -> Deal:
    return create_deal(bound=True)


def test_create_deal_has_qualified_status():
    deal = create_deal()

    assert deal.status is DealStatus.QUALIFIED
    assert deal.version == 1
    assert deal.source_of_truth == "deal"


def test_create_deal_has_authoritative_identity():
    deal = create_deal()

    assert deal.deal_id == "deal-001"
    assert deal.tenant_id == "tenant-001"
    assert deal.customer_id == "customer-001"
    assert deal.broker_id == "broker-001"
    assert deal.identity_key == "tenant-001:deal-001"


def test_creation_history_is_recorded():
    deal = create_deal()

    assert len(deal.history) == 1
    assert deal.history[0].from_status is None
    assert deal.history[0].to_status is DealStatus.QUALIFIED
    assert deal.history[0].version == 1
    assert deal.history[0].reason == "DEAL_CREATED"


def test_opportunity_can_be_bound():
    deal = create_deal()

    updated = deal.bind_opportunity(
        builder_id="builder-001",
        project_id="project-001",
        unit_id="unit-001",
        tenant_id="tenant-001",
        expected_version=1,
        at=AT,
    )

    assert updated.opportunity_bound
    assert updated.builder_id == "builder-001"
    assert updated.project_id == "project-001"
    assert updated.unit_id == "unit-001"
    assert updated.version == 2


def test_same_opportunity_binding_is_idempotent():
    deal = bound_deal()

    updated = deal.bind_opportunity(
        builder_id="builder-001",
        project_id="project-001",
        unit_id="unit-001",
        tenant_id="tenant-001",
        expected_version=1,
        at=AT,
    )

    assert updated is deal


def test_opportunity_cannot_be_silently_substituted():
    deal = bound_deal()

    with pytest.raises(DealReferenceConflictError):
        deal.bind_opportunity(
            builder_id="builder-002",
            project_id="project-002",
            unit_id="unit-002",
            tenant_id="tenant-001",
            expected_version=1,
            at=AT,
        )


def test_wrong_tenant_cannot_bind_opportunity():
    deal = create_deal()

    with pytest.raises(DealTenantError):
        deal.bind_opportunity(
            builder_id="builder-001",
            project_id="project-001",
            unit_id="unit-001",
            tenant_id="tenant-999",
            expected_version=1,
        )


def test_full_nominal_lifecycle():
    deal = bound_deal()

    path = (
        DealStatus.MATCHED,
        DealStatus.VISIT_PENDING,
        DealStatus.VISITED,
        DealStatus.OFFERED,
        DealStatus.NEGOTIATING,
        DealStatus.BOOKING_PENDING,
        DealStatus.BOOKED,
        DealStatus.AGREEMENT_PENDING,
        DealStatus.AGREED,
        DealStatus.REGISTRATION_PENDING,
        DealStatus.REGISTERED,
        DealStatus.COMPLETION_PENDING,
        DealStatus.COMPLETED,
    )

    current = deal

    for expected_version, status in enumerate(path, start=2):
        current = current.transition(
            status,
            tenant_id="tenant-001",
            expected_version=expected_version - 1,
            at=AT,
        )

        assert current.status is status
        assert current.version == expected_version

    assert current.status is DealStatus.COMPLETED
    assert current.is_terminal


def test_negotiation_can_return_to_offered():
    deal = bound_deal()

    current = deal.transition(
        DealStatus.MATCHED,
        tenant_id="tenant-001",
        expected_version=1,
        at=AT,
    )
    current = current.transition(
        DealStatus.VISIT_PENDING,
        tenant_id="tenant-001",
        expected_version=2,
        at=AT,
    )
    current = current.transition(
        DealStatus.VISITED,
        tenant_id="tenant-001",
        expected_version=3,
        at=AT,
    )
    current = current.transition(
        DealStatus.OFFERED,
        tenant_id="tenant-001",
        expected_version=4,
        at=AT,
    )
    current = current.transition(
        DealStatus.NEGOTIATING,
        tenant_id="tenant-001",
        expected_version=5,
        at=AT,
    )

    current = current.transition(
        DealStatus.OFFERED,
        tenant_id="tenant-001",
        expected_version=6,
        at=AT,
    )

    assert current.status is DealStatus.OFFERED
    assert current.version == 7


def test_invalid_transition_is_blocked():
    deal = bound_deal()

    with pytest.raises(DealTransitionError):
        deal.transition(
            DealStatus.BOOKED,
            tenant_id="tenant-001",
            expected_version=1,
            at=AT,
        )


def test_match_requires_opportunity_binding():
    deal = create_deal()

    with pytest.raises(DealTransitionError):
        deal.transition(
            DealStatus.MATCHED,
            tenant_id="tenant-001",
            expected_version=1,
            at=AT,
        )


def test_wrong_tenant_cannot_transition():
    deal = bound_deal()

    with pytest.raises(DealTenantError):
        deal.transition(
            DealStatus.MATCHED,
            tenant_id="tenant-999",
            expected_version=1,
            at=AT,
        )


def test_stale_version_is_rejected():
    deal = bound_deal()

    with pytest.raises(DealConcurrencyError):
        deal.transition(
            DealStatus.MATCHED,
            tenant_id="tenant-001",
            expected_version=99,
            at=AT,
        )


def test_invalid_expected_version_is_rejected():
    deal = bound_deal()

    with pytest.raises(DealConcurrencyError):
        deal.transition(
            DealStatus.MATCHED,
            tenant_id="tenant-001",
            expected_version=0,
            at=AT,
        )


def test_version_increments_exactly_once_per_transition():
    deal = bound_deal()

    updated = deal.transition(
        DealStatus.MATCHED,
        tenant_id="tenant-001",
        expected_version=1,
        at=AT,
    )

    assert updated.version == deal.version + 1


@pytest.mark.parametrize(
    "terminal_status",
    [
        DealStatus.CANCELLED,
        DealStatus.EXPIRED,
        DealStatus.REJECTED,
        DealStatus.FRAUD_BLOCKED,
    ],
)
def test_active_deal_can_enter_terminal_exception(terminal_status):
    deal = bound_deal()

    updated = deal.transition(
        terminal_status,
        tenant_id="tenant-001",
        expected_version=1,
        at=AT,
    )

    assert updated.status is terminal_status
    assert updated.is_terminal


def test_expired_is_rejected_after_completion():
    current = bound_deal()

    lifecycle = (
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

    for target in lifecycle:
        current = current.transition(
            target,
            tenant_id="tenant-001",
            expected_version=current.version,
            at=AT,
        )

    with pytest.raises(DealTransitionError):
        current.transition(
            DealStatus.EXPIRED,
            tenant_id="tenant-001",
            expected_version=current.version,
            at=AT,
        )
def test_dispute_is_allowed_after_booking():
    deal = bound_deal()

    current = deal.transition(
        DealStatus.MATCHED,
        tenant_id="tenant-001",
        expected_version=1,
        at=AT,
    )
    current = current.transition(
        DealStatus.VISIT_PENDING,
        tenant_id="tenant-001",
        expected_version=2,
        at=AT,
    )
    current = current.transition(
        DealStatus.VISITED,
        tenant_id="tenant-001",
        expected_version=3,
        at=AT,
    )
    current = current.transition(
        DealStatus.OFFERED,
        tenant_id="tenant-001",
        expected_version=4,
        at=AT,
    )
    current = current.transition(
        DealStatus.BOOKING_PENDING,
        tenant_id="tenant-001",
        expected_version=5,
        at=AT,
    )
    current = current.transition(
        DealStatus.BOOKED,
        tenant_id="tenant-001",
        expected_version=6,
        at=AT,
    )

    disputed = current.transition(
        DealStatus.DISPUTED,
        tenant_id="tenant-001",
        expected_version=7,
        at=AT,
    )

    assert disputed.status is DealStatus.DISPUTED
    assert disputed.is_terminal


def test_dispute_is_blocked_before_booking():
    deal = bound_deal()

    with pytest.raises(DealTransitionError):
        deal.transition(
            DealStatus.DISPUTED,
            tenant_id="tenant-001",
            expected_version=1,
            at=AT,
        )


def test_completed_deal_is_immutable():
    deal = bound_deal()

    current = deal

    for status in (
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
            status,
            tenant_id="tenant-001",
            expected_version=current.version,
            at=AT,
        )

    with pytest.raises(DealTransitionError):
        current.transition(
            DealStatus.CANCELLED,
            tenant_id="tenant-001",
            expected_version=current.version,
            at=AT,
        )


def test_history_preserves_every_transition():
    deal = bound_deal()

    current = deal.transition(
        DealStatus.MATCHED,
        tenant_id="tenant-001",
        expected_version=1,
        reason="MATCH_CONFIRMED",
        at=AT,
    )

    current = current.transition(
        DealStatus.VISIT_PENDING,
        tenant_id="tenant-001",
        expected_version=2,
        reason="VISIT_REQUESTED",
        at=AT,
    )

    assert len(current.history) == 3

    assert current.history[1].to_status is DealStatus.MATCHED
    assert current.history[1].reason == "MATCH_CONFIRMED"

    assert current.history[2].from_status is DealStatus.MATCHED
    assert current.history[2].to_status is DealStatus.VISIT_PENDING


def test_history_is_immutable():
    deal = create_deal()

    with pytest.raises(AttributeError):
        deal.history.append(None)  # type: ignore[attr-defined]


def test_timestamps_are_normalized_to_utc():
    deal = Deal.create(
        tenant_id="tenant-001",
        customer_id="customer-001",
        broker_id="broker-001",
        deal_id="deal-utc",
        at="2026-09-23T10:00:00+05:30",
    )

    assert deal.created_at.tzinfo is not None
    assert deal.created_at.utcoffset() == timezone.utc.utcoffset(
        deal.created_at
    )


def test_to_dict_is_serializable():
    deal = bound_deal()

    data = deal.to_dict()

    assert data["deal_id"] == "deal-001"
    assert data["identity_key"] == "tenant-001:deal-001"
    assert data["tenant_id"] == "tenant-001"
    assert data["status"] == "QUALIFIED"
    assert data["version"] == 1
    assert data["source_of_truth"] == "deal"
    assert len(data["history"]) == 1


def test_missing_required_identity_is_rejected():
    with pytest.raises(DealValidationError):
        Deal.create(
            tenant_id="tenant-001",
            customer_id="",
            broker_id="broker-001",
            at=AT,
        )


def test_invalid_source_of_truth_is_rejected():
    deal = create_deal()

    with pytest.raises(DealValidationError):
        Deal(
            **{
                **deal.__dict__,
                "source_of_truth": "inventory",
            }
        )


def test_references_persist_through_lifecycle():
    deal = bound_deal()

    updated = deal.transition(
        DealStatus.MATCHED,
        tenant_id="tenant-001",
        expected_version=1,
        at=AT,
    )

    assert updated.builder_id == "builder-001"
    assert updated.project_id == "project-001"
    assert updated.unit_id == "unit-001"


def test_created_and_updated_timestamps_are_consistent():
    deal = create_deal()

    assert deal.updated_at == deal.created_at

    updated = deal.bind_opportunity(
        builder_id="builder-001",
        project_id="project-001",
        unit_id="unit-001",
        tenant_id="tenant-001",
        expected_version=1,
        at="2026-09-23T11:00:00+00:00",
    )

    assert updated.updated_at > updated.created_at


def test_history_versions_are_monotonic():
    deal = bound_deal()

    current = deal.transition(
        DealStatus.MATCHED,
        tenant_id="tenant-001",
        expected_version=1,
        at=AT,
    )

    current = current.transition(
        DealStatus.VISIT_PENDING,
        tenant_id="tenant-001",
        expected_version=2,
        at=AT,
    )

    versions = [entry.version for entry in current.history]

    assert versions == sorted(versions)
    assert versions == [1, 2, 3]


