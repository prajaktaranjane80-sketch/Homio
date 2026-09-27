from __future__ import annotations

import pytest

from AUTONOMY_ENGINE.core.inventory import (
    AvailabilityState,
    Inventory,
    InventoryDomainError,
    InventoryIdentity,
    InventoryProjectViolation,
    InventoryTenantViolation,
    InventoryType,
    LifecycleState,
)


def test_development_identity_forbids_children() -> None:
    with pytest.raises(InventoryDomainError):
        InventoryIdentity(
            inventory_id="inv-1",
            tenant_id="tenant-1",
            inventory_type=InventoryType.DEVELOPMENT,
            developer_id="dev-1",
            project_id="proj-1",
            property_id="prop-1",
        )


def test_property_identity_requires_property_and_forbids_unit() -> None:
    with pytest.raises(InventoryDomainError):
        InventoryIdentity(
            inventory_id="inv-1",
            tenant_id="tenant-1",
            inventory_type=InventoryType.PROPERTY,
            developer_id="dev-1",
            project_id="proj-1",
        )

    with pytest.raises(InventoryDomainError):
        InventoryIdentity(
            inventory_id="inv-1",
            tenant_id="tenant-1",
            inventory_type=InventoryType.PROPERTY,
            developer_id="dev-1",
            project_id="proj-1",
            property_id="prop-1",
            unit_id="unit-1",
        )


def test_unit_identity_requires_property_and_unit() -> None:
    identity = InventoryIdentity(
        inventory_id="inv-1",
        tenant_id="tenant-1",
        inventory_type=InventoryType.UNIT,
        developer_id="dev-1",
        project_id="proj-1",
        property_id="prop-1",
        unit_id="unit-1",
    )

    assert identity.inventory_type is InventoryType.UNIT
    assert identity.project_id == "proj-1"
    assert identity.property_id == "prop-1"
    assert identity.unit_id == "unit-1"


def test_identity_fingerprint_is_deterministic() -> None:
    kwargs = {
        "inventory_id": "inv-1",
        "tenant_id": "tenant-1",
        "inventory_type": InventoryType.UNIT,
        "developer_id": "dev-1",
        "project_id": "proj-1",
        "property_id": "prop-1",
        "unit_id": "unit-1",
    }

    first = InventoryIdentity(**kwargs)
    second = InventoryIdentity(**kwargs)

    assert first.fingerprint == second.fingerprint
    assert first.identity_key == second.identity_key


def test_identity_fingerprint_changes_when_identity_changes() -> None:
    base = InventoryIdentity(
        inventory_id="inv-1",
        tenant_id="tenant-1",
        inventory_type=InventoryType.UNIT,
        developer_id="dev-1",
        project_id="proj-1",
        property_id="prop-1",
        unit_id="unit-1",
    )

    changed = InventoryIdentity(
        inventory_id="inv-2",
        tenant_id="tenant-1",
        inventory_type=InventoryType.UNIT,
        developer_id="dev-1",
        project_id="proj-1",
        property_id="prop-1",
        unit_id="unit-1",
    )

    assert base.fingerprint != changed.fingerprint


def test_identity_is_immutable() -> None:
    identity = InventoryIdentity(
        inventory_id="inv-1",
        tenant_id="tenant-1",
        inventory_type=InventoryType.DEVELOPMENT,
        developer_id="dev-1",
        project_id="proj-1",
    )

    with pytest.raises(Exception):
        identity.project_id = "other"


def test_inventory_creation_has_safe_initial_state() -> None:
    inventory = Inventory.create(
        tenant_id="tenant-1",
        developer_id="dev-1",
        project_id="proj-1",
        inventory_type=InventoryType.UNIT,
        property_id="prop-1",
        unit_id="unit-1",
        name="Tower A / 1201",
        inventory_id="inv-1",
        at="2026-09-27T12:00:00+00:00",
    )

    assert inventory.lifecycle is LifecycleState.DRAFT
    assert inventory.availability is AvailabilityState.UNAVAILABLE
    assert inventory.version == 1
    assert inventory.identity_fingerprint


def test_tenant_boundary_is_fail_closed() -> None:
    inventory = Inventory.create(
        tenant_id="tenant-1",
        developer_id="dev-1",
        project_id="proj-1",
        inventory_type=InventoryType.DEVELOPMENT,
        name="Project",
        inventory_id="inv-1",
    )

    with pytest.raises(InventoryTenantViolation):
        inventory.assert_tenant("tenant-2")


def test_project_boundary_is_fail_closed() -> None:
    inventory = Inventory.create(
        tenant_id="tenant-1",
        developer_id="dev-1",
        project_id="proj-1",
        inventory_type=InventoryType.DEVELOPMENT,
        name="Project",
        inventory_id="inv-1",
    )

    with pytest.raises(InventoryProjectViolation):
        inventory.assert_project("proj-2")


def test_created_event_contains_immutable_identity_reference() -> None:
    inventory = Inventory.create(
        tenant_id="tenant-1",
        developer_id="dev-1",
        project_id="proj-1",
        inventory_type=InventoryType.PROPERTY,
        property_id="prop-1",
        name="Tower A",
        inventory_id="inv-1",
    )

    event = inventory.created_event(
        at="2026-09-27T12:00:00+00:00",
    )

    assert event.event_type == "INVENTORY_CREATED"
    assert event.inventory_id == inventory.inventory_id
    assert event.tenant_id == inventory.tenant_id
    assert event.inventory_version == inventory.version
    assert (
        event.payload["identity_fingerprint"]
        == inventory.identity_fingerprint
    )


def test_serialization_exposes_canonical_identity() -> None:
    inventory = Inventory.create(
        tenant_id="tenant-1",
        developer_id="dev-1",
        project_id="proj-1",
        inventory_type=InventoryType.UNIT,
        property_id="prop-1",
        unit_id="unit-1",
        name="1201",
        inventory_id="inv-1",
    )

    payload = inventory.to_dict()

    assert payload["identity"]["inventory_id"] == "inv-1"
    assert payload["identity"]["tenant_id"] == "tenant-1"
    assert payload["identity"]["project_id"] == "proj-1"
    assert payload["identity"]["property_id"] == "prop-1"
    assert payload["identity"]["unit_id"] == "unit-1"
    assert payload["identity_fingerprint"] == inventory.identity_fingerprint
