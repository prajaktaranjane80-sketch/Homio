from __future__ import annotations

import pytest

from AUTONOMY_ENGINE.core.inventory import (
    Inventory,
    InventoryDomainError,
    InventoryProjectViolation,
    InventoryTenantViolation,
    InventoryType,
)


@pytest.fixture
def inventory() -> Inventory:
    return Inventory.create(
        tenant_id="tenant-001",
        project_id="project-001",
        inventory_code="UNIT-001",
        inventory_type=InventoryType.RESIDENTIAL_UNIT,
        name="Test Unit",
        at="2026-08-29T10:00:00+00:00",
    )


def test_inventory_creation_is_tenant_and_project_scoped(
    inventory: Inventory,
) -> None:
    assert inventory.tenant_id == "tenant-001"
    assert inventory.project_id == "project-001"
    assert inventory.version == 1


def test_inventory_identity_is_project_scoped(
    inventory: Inventory,
) -> None:
    assert inventory.identity_key == (
        "tenant-001:project-001:UNIT-001"
    )


def test_inventory_supports_all_approved_types() -> None:
    for inventory_type in InventoryType:
        inventory = Inventory.create(
            tenant_id="tenant-001",
            project_id="project-001",
            inventory_code="UNIT-001",
            inventory_type=inventory_type,
            name="Test Inventory",
        )

        assert inventory.inventory_type is inventory_type


@pytest.mark.parametrize(
    "field",
    [
        "tenant_id",
        "project_id",
        "inventory_code",
        "name",
    ],
)
def test_required_fields_fail_closed(field: str) -> None:
    values = {
        "tenant_id": "tenant-001",
        "project_id": "project-001",
        "inventory_code": "UNIT-001",
        "inventory_type": InventoryType.RESIDENTIAL_UNIT,
        "name": "Test Unit",
    }

    values[field] = ""

    with pytest.raises(InventoryDomainError):
        Inventory.create(**values)


@pytest.mark.parametrize(
    "code",
    [
        "unit-001",
        "U",
        "bad code",
        "UNIT/001",
    ],
)
def test_inventory_code_is_strictly_validated(code: str) -> None:
    with pytest.raises(InventoryDomainError):
        Inventory.create(
            tenant_id="tenant-001",
            project_id="project-001",
            inventory_code=code,
            inventory_type=InventoryType.RESIDENTIAL_UNIT,
            name="Test Unit",
        )


def test_cross_tenant_access_is_blocked(
    inventory: Inventory,
) -> None:
    with pytest.raises(InventoryTenantViolation):
        inventory.assert_tenant("tenant-999")


def test_cross_project_access_is_blocked(
    inventory: Inventory,
) -> None:
    with pytest.raises(InventoryProjectViolation):
        inventory.assert_project("project-999")


def test_touch_is_deterministic_and_versioned(
    inventory: Inventory,
) -> None:
    updated, event = inventory.touch(
        tenant_id="tenant-001",
        project_id="project-001",
        at="2026-08-29T11:00:00+00:00",
    )

    assert updated.version == 2
    assert updated.inventory_id == inventory.inventory_id
    assert updated.project_id == inventory.project_id

    assert event.inventory_id == inventory.inventory_id
    assert event.project_id == inventory.project_id
    assert event.tenant_id == inventory.tenant_id
    assert event.inventory_version == 2
    assert event.event_type == "INVENTORY_VERSION_CHANGED"


def test_serialization_contains_authoritative_identity(
    inventory: Inventory,
) -> None:
    data = inventory.to_dict()

    assert data["inventory_id"] == inventory.inventory_id
    assert data["tenant_id"] == inventory.tenant_id
    assert data["project_id"] == inventory.project_id
    assert data["inventory_code"] == inventory.inventory_code
    assert data["source_of_truth"] == "inventory"


def test_inventory_is_immutable(
    inventory: Inventory,
) -> None:
    with pytest.raises(Exception):
        inventory.name = "Changed"  # type: ignore[misc]
