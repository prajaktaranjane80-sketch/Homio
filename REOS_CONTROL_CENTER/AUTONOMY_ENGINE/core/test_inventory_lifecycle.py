from __future__ import annotations

import pytest

from AUTONOMY_ENGINE.core.inventory import (
    Inventory,
    InventoryLifecycle,
    InventoryTransitionError,
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


def test_inventory_starts_in_draft(inventory: Inventory) -> None:
    assert inventory.lifecycle is InventoryLifecycle.DRAFT
    assert inventory.version == 1


def test_valid_lifecycle_transition_is_versioned(
    inventory: Inventory,
) -> None:
    updated, event = inventory.transition(
        InventoryLifecycle.ONBOARDING,
        tenant_id="tenant-001",
        project_id="project-001",
        at="2026-08-29T10:01:00+00:00",
    )

    assert updated.lifecycle is InventoryLifecycle.ONBOARDING
    assert updated.version == 2
    assert event.event_type == "INVENTORY_LIFECYCLE_CHANGED"
    assert event.inventory_version == 2
    assert event.payload["from"] == "DRAFT"
    assert event.payload["to"] == "ONBOARDING"


def test_invalid_lifecycle_transition_is_blocked(
    inventory: Inventory,
) -> None:
    with pytest.raises(InventoryTransitionError):
        inventory.transition(
            InventoryLifecycle.ACTIVE,
            tenant_id="tenant-001",
            project_id="project-001",
        )


def test_archived_inventory_is_terminal(
    inventory: Inventory,
) -> None:
    onboarding, _ = inventory.transition(
        InventoryLifecycle.ONBOARDING,
        tenant_id="tenant-001",
        project_id="project-001",
    )
    archived, _ = onboarding.transition(
        InventoryLifecycle.ARCHIVED,
        tenant_id="tenant-001",
        project_id="project-001",
    )

    assert archived.lifecycle is InventoryLifecycle.ARCHIVED

    with pytest.raises(InventoryTransitionError):
        archived.transition(
            InventoryLifecycle.ACTIVE,
            tenant_id="tenant-001",
            project_id="project-001",
        )


def test_cross_tenant_lifecycle_transition_is_blocked(
    inventory: Inventory,
) -> None:
    with pytest.raises(Exception) as exc:
        inventory.transition(
            InventoryLifecycle.ONBOARDING,
            tenant_id="tenant-999",
            project_id="project-001",
        )

    assert "tenant" in str(exc.value).lower()


def test_cross_project_lifecycle_transition_is_blocked(
    inventory: Inventory,
) -> None:
    with pytest.raises(Exception) as exc:
        inventory.transition(
            InventoryLifecycle.ONBOARDING,
            tenant_id="tenant-001",
            project_id="project-999",
        )

    assert "project" in str(exc.value).lower()


def test_lifecycle_transition_preserves_inventory_identity(
    inventory: Inventory,
) -> None:
    updated, _ = inventory.transition(
        InventoryLifecycle.ONBOARDING,
        tenant_id="tenant-001",
        project_id="project-001",
    )

    assert updated.inventory_id == inventory.inventory_id
    assert updated.tenant_id == inventory.tenant_id
    assert updated.project_id == inventory.project_id
    assert updated.inventory_code == inventory.inventory_code