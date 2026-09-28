from __future__ import annotations

from datetime import datetime, timezone

import pytest

from AUTONOMY_ENGINE.core.deal import (
    Deal,
    DealReferenceConflictError,
)
from AUTONOMY_ENGINE.core.deal_ownership_integration import (
    DealOwnershipBinding,
    DealOwnershipTenantError,
    DealOwnershipValidationError,
)


AT = datetime(2026, 9, 23, 10, 0, tzinfo=timezone.utc)


@pytest.fixture
def deal() -> Deal:
    return Deal.create(
        tenant_id="tenant-001",
        customer_id="customer-001",
        broker_id="broker-001",
        at=AT.isoformat(),
    )


def test_ownership_binding_is_created_and_versioned(deal: Deal):
    updated = deal.bind_ownership(
        "binding-001",
        lead_id="lead-001",
        ownership_record_id="ownership-001",
        owner_id="broker-001",
        tenant_id="tenant-001",
        expected_version=1,
        at=AT,
    )

    assert updated.ownership_binding is not None
    assert updated.ownership_binding.deal_id == updated.deal_id
    assert updated.ownership_binding.lead_id == "lead-001"
    assert updated.ownership_binding.ownership_record_id == "ownership-001"
    assert updated.ownership_binding.owner_id == "broker-001"
    assert updated.ownership_binding.authority == "ARCH-011"
    assert updated.version == 2


def test_same_ownership_binding_is_idempotent(deal: Deal):
    updated = deal.bind_ownership(
        "binding-001",
        lead_id="lead-001",
        ownership_record_id="ownership-001",
        owner_id="broker-001",
        tenant_id="tenant-001",
        expected_version=1,
        at=AT,
    )

    again = updated.bind_ownership(
        "binding-001",
        lead_id="lead-001",
        ownership_record_id="ownership-001",
        owner_id="broker-001",
        tenant_id="tenant-001",
        expected_version=updated.version,
        at=AT,
    )

    assert again is updated


def test_silent_ownership_substitution_is_blocked(deal: Deal):
    updated = deal.bind_ownership(
        "binding-001",
        lead_id="lead-001",
        ownership_record_id="ownership-001",
        owner_id="broker-001",
        tenant_id="tenant-001",
        expected_version=1,
        at=AT,
    )

    with pytest.raises(DealReferenceConflictError):
        updated.bind_ownership(
            "binding-002",
            lead_id="lead-002",
            ownership_record_id="ownership-002",
            owner_id="broker-002",
            tenant_id="tenant-001",
            expected_version=updated.version,
            at=AT,
        )


def test_cross_tenant_binding_is_blocked(deal: Deal):
    from AUTONOMY_ENGINE.core.deal import DealTenantError

    with pytest.raises(DealTenantError):
        deal.bind_ownership(
            "binding-001",
            lead_id="lead-001",
            ownership_record_id="ownership-001",
            owner_id="broker-001",
            tenant_id="tenant-002",
            expected_version=deal.version,
            at=AT,
        )

def test_invalid_ownership_reference_is_rejected(deal: Deal):
    with pytest.raises(DealOwnershipValidationError):
        deal.bind_ownership(
            "binding-001",
            lead_id="",
            ownership_record_id="ownership-001",
            owner_id="broker-001",
            tenant_id="tenant-001",
            expected_version=1,
            at=AT,
        )


def test_authority_cannot_be_replaced():
    with pytest.raises(DealOwnershipValidationError):
        DealOwnershipBinding(
            binding_id="binding-001",
            deal_id="deal-001",
            tenant_id="tenant-001",
            lead_id="lead-001",
            ownership_record_id="ownership-001",
            owner_id="broker-001",
            bound_at=AT,
            authority="CUSTOM_ENGINE",
        )


def test_ownership_binding_is_immutable(deal: Deal):
    updated = deal.bind_ownership(
        "binding-001",
        lead_id="lead-001",
        ownership_record_id="ownership-001",
        owner_id="broker-001",
        tenant_id="tenant-001",
        expected_version=1,
        at=AT,
    )

    with pytest.raises(Exception):
        updated.ownership_binding.owner_id = "broker-002"


def test_ownership_reference_is_tenant_scoped(deal: Deal):
    updated = deal.bind_ownership(
        "binding-001",
        lead_id="lead-001",
        ownership_record_id="ownership-001",
        owner_id="broker-001",
        tenant_id="tenant-001",
        expected_version=1,
        at=AT,
    )

    assert (
        updated.ownership_binding.reference_key
        == f"tenant-001:{deal.deal_id}:ownership-001"
    )


def test_ownership_serialization_is_traceable(deal: Deal):
    updated = deal.bind_ownership(
        "binding-001",
        lead_id="lead-001",
        ownership_record_id="ownership-001",
        owner_id="broker-001",
        tenant_id="tenant-001",
        expected_version=1,
        at=AT,
    )

    payload = updated.to_dict()

    assert payload["ownership_binding"]["deal_id"] == deal.deal_id
    assert payload["ownership_binding"]["lead_id"] == "lead-001"
    assert payload["ownership_binding"]["ownership_record_id"] == "ownership-001"
    assert payload["ownership_binding"]["owner_id"] == "broker-001"
    assert payload["ownership_binding"]["authority"] == "ARCH-011"


def test_terminal_deal_cannot_bind_ownership():
    from AUTONOMY_ENGINE.core.deal import DealStatus

    current = Deal.create(
        tenant_id="tenant-001",
        customer_id="customer-001",
        broker_id="broker-001",
        builder_id="builder-001",
        project_id="project-001",
        unit_id="unit-001",
        at=AT.isoformat(),
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

    with pytest.raises(DealReferenceConflictError):
        current.bind_ownership(
            "binding-terminal",
            lead_id="lead-001",
            ownership_record_id="ownership-001",
            owner_id="broker-001",
            tenant_id="tenant-001",
            expected_version=current.version,
            at=AT,
        )


def test_existing_deal_party_reference_is_not_duplicated(deal: Deal):
    updated = deal.bind_ownership(
        "binding-001",
        lead_id="lead-001",
        ownership_record_id="ownership-001",
        owner_id="broker-001",
        tenant_id="tenant-001",
        expected_version=1,
        at=AT,
    )

    assert updated.broker_id == "broker-001"
    assert updated.ownership_binding.owner_id == "broker-001"


def test_stale_ownership_binding_is_blocked(deal: Deal):
    with pytest.raises(Exception):
        deal.bind_ownership(
            "binding-001",
            lead_id="lead-001",
            ownership_record_id="ownership-001",
            owner_id="broker-001",
            tenant_id="tenant-001",
            expected_version=99,
            at=AT,
        )





