from __future__ import annotations

import pytest

from AUTONOMY_ENGINE.core.inventory import Inventory, InventoryType
from AUTONOMY_ENGINE.core.inventory_history import (
    InventoryHistory,
    InventoryHistoryError,
    InventoryHistoryScopeError,
    InventoryHistoryVersionError,
)


@pytest.fixture
def inventory() -> Inventory:
    return Inventory.create(
        tenant_id="tenant-001",
        project_id="project-001",
        inventory_code="UNIT-001",
        inventory_type=InventoryType.RESIDENTIAL_UNIT,
        name="Unit 001",
        at="2026-08-30T10:00:00+00:00",
    )


def test_history_can_be_created_from_inventory(
    inventory: Inventory,
) -> None:
    history = InventoryHistory.from_inventory(
        inventory,
        at="2026-08-30T10:01:00+00:00",
    )

    assert history.inventory_id == inventory.inventory_id
    assert history.tenant_id == inventory.tenant_id
    assert history.project_id == inventory.project_id
    assert history.inventory_version == inventory.version
    assert history.snapshot["inventory_id"] == inventory.inventory_id


def test_history_is_immutable_snapshot(
    inventory: Inventory,
) -> None:
    history = InventoryHistory.from_inventory(inventory)

    assert history.snapshot["version"] == 1
    assert history.inventory_version == 1


def test_history_matches_inventory(
    inventory: Inventory,
) -> None:
    history = InventoryHistory.from_inventory(inventory)

    history.assert_matches_inventory(inventory)


def test_cross_tenant_history_scope_is_blocked(
    inventory: Inventory,
) -> None:
    history = InventoryHistory.from_inventory(inventory)

    with pytest.raises(InventoryHistoryScopeError):
        history.assert_scope(
            tenant_id="tenant-999",
            project_id="project-001",
            inventory_id=inventory.inventory_id,
        )


def test_cross_project_history_scope_is_blocked(
    inventory: Inventory,
) -> None:
    history = InventoryHistory.from_inventory(inventory)

    with pytest.raises(InventoryHistoryScopeError):
        history.assert_scope(
            tenant_id="tenant-001",
            project_id="project-999",
            inventory_id=inventory.inventory_id,
        )


def test_wrong_inventory_history_scope_is_blocked(
    inventory: Inventory,
) -> None:
    history = InventoryHistory.from_inventory(inventory)

    with pytest.raises(InventoryHistoryScopeError):
        history.assert_scope(
            tenant_id="tenant-001",
            project_id="project-001",
            inventory_id="other-inventory",
        )


def test_stale_history_version_is_blocked(
    inventory: Inventory,
) -> None:
    history = InventoryHistory.from_inventory(inventory)

    updated, _ = inventory.touch(
        tenant_id="tenant-001",
        project_id="project-001",
    )

    with pytest.raises(InventoryHistoryVersionError):
        history.assert_matches_inventory(updated)


def test_history_event_serializes(
    inventory: Inventory,
) -> None:
    history = InventoryHistory.from_inventory(inventory)

    event = history.to_event()
    data = event.to_dict()

    assert data["event_type"] == "INVENTORY_HISTORY_RECORDED"
    assert data["inventory_id"] == inventory.inventory_id
    assert data["inventory_version"] == 1


def test_history_serializes_canonically(
    inventory: Inventory,
) -> None:
    history = InventoryHistory.from_inventory(inventory)

    data = history.to_dict()

    assert data["history_id"] == history.history_id
    assert data["inventory_id"] == inventory.inventory_id
    assert data["tenant_id"] == "tenant-001"
    assert data["project_id"] == "project-001"
    assert data["inventory_version"] == 1
    assert data["source_of_truth"] == "inventory_history"