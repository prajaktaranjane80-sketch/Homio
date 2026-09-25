from __future__ import annotations

import pytest

from AUTONOMY_ENGINE.core.inventory import (
    Inventory,
    InventoryAvailability,
    InventoryAvailabilityTransitionError,
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
        name="Unit 001",
        at="2026-08-29T10:00:00+00:00",
    )


def test_inventory_starts_available(inventory: Inventory) -> None:
    assert inventory.availability is InventoryAvailability.AVAILABLE


def test_all_availability_states_exist() -> None:
    assert set(InventoryAvailability) == {
        InventoryAvailability.AVAILABLE,
        InventoryAvailability.RESERVED,
        InventoryAvailability.SOLD,
        InventoryAvailability.UNAVAILABLE,
    }


@pytest.mark.parametrize(
    ("target", "expected_version"),
    [
        (InventoryAvailability.RESERVED, 2),
        (InventoryAvailability.SOLD, 2),
        (InventoryAvailability.UNAVAILABLE, 2),
    ],
)
def test_available_transitions_are_versioned(
    inventory: Inventory,
    target: InventoryAvailability,
    expected_version: int,
) -> None:
    updated, event = inventory.set_availability(
        target,
        tenant_id="tenant-001",
        project_id="project-001",
        at="2026-08-29T10:01:00+00:00",
    )

    assert updated.availability is target
    assert updated.version == expected_version
    assert updated.inventory_id == inventory.inventory_id
    assert updated.project_id == inventory.project_id
    assert updated.tenant_id == inventory.tenant_id

    assert event.event_type == "INVENTORY_AVAILABILITY_CHANGED"
    assert event.inventory_id == inventory.inventory_id
    assert event.project_id == inventory.project_id
    assert event.tenant_id == inventory.tenant_id
    assert event.inventory_version == updated.version
    assert event.payload["from"] == "AVAILABLE"
    assert event.payload["to"] == target.value


@pytest.mark.parametrize(
    ("current", "target"),
    [
        (InventoryAvailability.RESERVED, InventoryAvailability.AVAILABLE),
        (InventoryAvailability.RESERVED, InventoryAvailability.SOLD),
        (InventoryAvailability.RESERVED, InventoryAvailability.UNAVAILABLE),
        (InventoryAvailability.SOLD, InventoryAvailability.UNAVAILABLE),
        (InventoryAvailability.UNAVAILABLE, InventoryAvailability.AVAILABLE),
    ],
)
def test_supported_transitions_work(
    inventory: Inventory,
    current: InventoryAvailability,
    target: InventoryAvailability,
) -> None:
    current_inventory, _ = inventory.set_availability(
        current,
        tenant_id="tenant-001",
        project_id="project-001",
        at="2026-08-29T10:01:00+00:00",
    )

    updated, _ = current_inventory.set_availability(
        target,
        tenant_id="tenant-001",
        project_id="project-001",
        at="2026-08-29T10:02:00+00:00",
    )

    assert updated.availability is target
    assert updated.version == current_inventory.version + 1


@pytest.mark.parametrize(
    ("current", "target"),
    [
        (InventoryAvailability.AVAILABLE, InventoryAvailability.AVAILABLE),
        (InventoryAvailability.RESERVED, InventoryAvailability.RESERVED),
        (InventoryAvailability.SOLD, InventoryAvailability.AVAILABLE),
        (InventoryAvailability.SOLD, InventoryAvailability.RESERVED),
        (InventoryAvailability.SOLD, InventoryAvailability.SOLD),
        (InventoryAvailability.UNAVAILABLE, InventoryAvailability.RESERVED),
        (InventoryAvailability.UNAVAILABLE, InventoryAvailability.SOLD),
        (InventoryAvailability.UNAVAILABLE, InventoryAvailability.UNAVAILABLE),
    ],
)
def test_unsupported_transitions_are_blocked(
    inventory: Inventory,
    current: InventoryAvailability,
    target: InventoryAvailability,
) -> None:
    if current is InventoryAvailability.AVAILABLE:
        current_inventory = inventory
    else:
        current_inventory, _ = inventory.set_availability(
            current,
            tenant_id="tenant-001",
            project_id="project-001",
            at="2026-08-29T10:01:00+00:00",
        )

    with pytest.raises(InventoryAvailabilityTransitionError):
        current_inventory.set_availability(
            target,
            tenant_id="tenant-001",
            project_id="project-001",
            at="2026-08-29T10:02:00+00:00",
        )


def test_cross_tenant_change_is_blocked(
    inventory: Inventory,
) -> None:
    with pytest.raises(InventoryTenantViolation):
        inventory.set_availability(
            InventoryAvailability.RESERVED,
            tenant_id="tenant-999",
            project_id="project-001",
        )


def test_cross_project_change_is_blocked(
    inventory: Inventory,
) -> None:
    with pytest.raises(InventoryProjectViolation):
        inventory.set_availability(
            InventoryAvailability.RESERVED,
            tenant_id="tenant-001",
            project_id="project-999",
        )


def test_availability_change_is_immutable(
    inventory: Inventory,
) -> None:
    updated, _ = inventory.set_availability(
        InventoryAvailability.RESERVED,
        tenant_id="tenant-001",
        project_id="project-001",
        at="2026-08-29T10:01:00+00:00",
    )

    assert inventory.availability is InventoryAvailability.AVAILABLE
    assert inventory.version == 1

    assert updated.availability is InventoryAvailability.RESERVED
    assert updated.version == 2


def test_availability_is_serialized_canonically(
    inventory: Inventory,
) -> None:
    updated, _ = inventory.set_availability(
        InventoryAvailability.RESERVED,
        tenant_id="tenant-001",
        project_id="project-001",
        at="2026-08-29T10:01:00+00:00",
    )

    data = updated.to_dict()

    assert data["inventory_id"] == inventory.inventory_id
    assert data["tenant_id"] == "tenant-001"
    assert data["project_id"] == "project-001"
    assert data["availability"] == "RESERVED"
    assert data["version"] == 2