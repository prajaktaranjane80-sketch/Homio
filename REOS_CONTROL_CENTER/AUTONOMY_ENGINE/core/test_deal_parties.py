from __future__ import annotations

import pytest

from AUTONOMY_ENGINE.core.deal import (
    Deal,
    DealConcurrencyError,
    DealPartyRelationship,
    DealPartyRole,
    DealReferenceConflictError,
    DealTenantError,
    DealValidationError,
)


AT = "2026-09-23T10:00:00+00:00"


@pytest.fixture
def deal() -> Deal:
    return Deal.create(
        tenant_id="tenant-001",
        customer_id="customer-001",
        broker_id="broker-001",
        at=AT,
    )


def test_required_customer_and_broker_relationships_are_exposed(deal: Deal):
    relationships = deal.party_relationships

    assert len(relationships) == 2
    assert deal.party_for(DealPartyRole.CUSTOMER) == "customer-001"
    assert deal.party_for(DealPartyRole.BROKER) == "broker-001"
    assert deal.party_for(DealPartyRole.BUILDER) is None


def test_relationships_are_tenant_and_deal_scoped(deal: Deal):
    keys = {item.relationship_key for item in deal.party_relationships}

    assert keys == {
        "tenant-001:" + deal.deal_id + ":CUSTOMER",
        "tenant-001:" + deal.deal_id + ":BROKER",
    }


def test_relationship_objects_are_immutable(deal: Deal):
    relationship = deal.party_relationships[0]

    with pytest.raises(Exception):
        relationship.party_id = "other-party"


def test_invalid_party_id_is_rejected(deal: Deal):
    with pytest.raises(DealValidationError):
        deal.bind_party(
            DealPartyRole.BUILDER,
            "",
            tenant_id="tenant-001",
            expected_version=deal.version,
            at=AT,
        )


def test_builder_can_be_bound_as_a_new_party(deal: Deal):
    updated = deal.bind_party(
        DealPartyRole.BUILDER,
        "builder-001",
        tenant_id="tenant-001",
        expected_version=deal.version,
        at=AT,
    )

    assert updated.builder_id == "builder-001"
    assert updated.party_for(DealPartyRole.BUILDER) == "builder-001"
    assert updated.version == 2


def test_same_party_binding_is_idempotent(deal: Deal):
    updated = deal.bind_party(
        DealPartyRole.CUSTOMER,
        "customer-001",
        tenant_id="tenant-001",
        expected_version=deal.version,
        at=AT,
    )

    assert updated is deal
    assert updated.version == deal.version


def test_existing_party_cannot_be_silently_replaced(deal: Deal):
    with pytest.raises(DealReferenceConflictError):
        deal.bind_party(
            DealPartyRole.BROKER,
            "broker-002",
            tenant_id="tenant-001",
            expected_version=deal.version,
            at=AT,
        )


def test_builder_cannot_be_silently_replaced(deal: Deal):
    updated = deal.bind_party(
        DealPartyRole.BUILDER,
        "builder-001",
        tenant_id="tenant-001",
        expected_version=deal.version,
        at=AT,
    )

    with pytest.raises(DealReferenceConflictError):
        updated.bind_party(
            DealPartyRole.BUILDER,
            "builder-002",
            tenant_id="tenant-001",
            expected_version=updated.version,
            at=AT,
        )


def test_cross_tenant_party_binding_is_blocked(deal: Deal):
    with pytest.raises(DealTenantError):
        deal.bind_party(
            DealPartyRole.BUILDER,
            "builder-001",
            tenant_id="tenant-002",
            expected_version=deal.version,
            at=AT,
        )


def test_stale_party_binding_is_blocked(deal: Deal):
    with pytest.raises(DealConcurrencyError):
        deal.bind_party(
            DealPartyRole.BUILDER,
            "builder-001",
            tenant_id="tenant-001",
            expected_version=999,
            at=AT,
        )


def test_party_relationship_serialization_is_stable(deal: Deal):
    relationship = deal.party_relationships[0]
    payload = relationship.to_dict()

    assert payload["deal_id"] == deal.deal_id
    assert payload["tenant_id"] == "tenant-001"
    assert payload["role"] == "CUSTOMER"
    assert payload["party_id"] == "customer-001"


def test_opportunity_builder_and_party_relationship_remain_consistent(deal: Deal):
    updated = deal.bind_opportunity(
        builder_id="builder-001",
        project_id="project-001",
        unit_id="unit-001",
        tenant_id="tenant-001",
        expected_version=deal.version,
        at=AT,
    )

    assert updated.party_for(DealPartyRole.BUILDER) == "builder-001"


def test_terminal_deal_cannot_change_party_relationship(deal: Deal):
    current = deal.bind_opportunity(
        builder_id="builder-001",
        project_id="project-001",
        unit_id="unit-001",
        tenant_id="tenant-001",
        expected_version=deal.version,
        at=AT,
    )

    current = current.transition(
        __import__("AUTONOMY_ENGINE.core.deal", fromlist=["DealStatus"]).DealStatus.MATCHED,
        tenant_id="tenant-001",
        expected_version=current.version,
        at=AT,
    )

    lifecycle = [
        "VISIT_PENDING",
        "VISITED",
        "OFFERED",
        "BOOKING_PENDING",
        "BOOKED",
        "AGREEMENT_PENDING",
        "AGREED",
        "REGISTRATION_PENDING",
        "REGISTERED",
        "COMPLETION_PENDING",
        "COMPLETED",
    ]

    DealStatus = __import__(
        "AUTONOMY_ENGINE.core.deal",
        fromlist=["DealStatus"],
    ).DealStatus

    for status in lifecycle:
        current = current.transition(
            DealStatus(status),
            tenant_id="tenant-001",
            expected_version=current.version,
            at=AT,
        )

    with pytest.raises(DealReferenceConflictError):
        current.bind_party(
            DealPartyRole.BUILDER,
            "builder-002",
            tenant_id="tenant-001",
            expected_version=current.version,
            at=AT,
        )


def test_relationship_type_is_explicit():
    relationship = DealPartyRelationship(
        deal_id="deal-001",
        tenant_id="tenant-001",
        role=DealPartyRole.CUSTOMER,
        party_id="customer-001",
    )

    assert relationship.role is DealPartyRole.CUSTOMER
