from __future__ import annotations

import pytest

from AUTONOMY_ENGINE.core.inventory import (
    Inventory,
    InventoryAvailability,
    InventoryType,
)
from AUTONOMY_ENGINE.core.inventory_concurrency import (
    InventoryConcurrencyGuard,
    InventoryConcurrencyOperation,
    InventoryConcurrencyScopeError,
    InventoryInvalidExpectedVersionError,
    InventoryStaleWriteError,
    assert_inventory_version,
)


@pytest.fixture
def inventory() -> Inventory:
    return Inventory.create(
        tenant_id="tenant-001",
        project_id="project-001",
        inventory_code="UNIT-001",
        inventory_type=InventoryType.RESIDENTIAL_UNIT,
        name="Unit 001",
        at="2026-08-31T10:00:00+00:00",
    )


def test_current_version_is_accepted(
    inventory: Inventory,
) -> None:
    receipt = assert_inventory_version(
        inventory,
        tenant_id="tenant-001",
        project_id="project-001",
        expected_version=1,
    )

    assert receipt.inventory_id == inventory.inventory_id
    assert receipt.expected_version == 1
    assert receipt.current_version == 1
    assert receipt.is_current is True


def test_stale_version_is_blocked(
    inventory: Inventory,
) -> None:
    updated, _ = inventory.touch(
        tenant_id="tenant-001",
        project_id="project-001",
        at="2026-08-31T10:01:00+00:00",
    )

    with pytest.raises(InventoryStaleWriteError):
        assert_inventory_version(
            updated,
            tenant_id="tenant-001",
            project_id="project-001",
            expected_version=1,
        )


def test_new_version_is_accepted_after_change(
    inventory: Inventory,
) -> None:
    updated, _ = inventory.touch(
        tenant_id="tenant-001",
        project_id="project-001",
    )

    receipt = assert_inventory_version(
        updated,
        tenant_id="tenant-001",
        project_id="project-001",
        expected_version=2,
    )

    assert receipt.current_version == 2
    assert receipt.expected_version == 2


def test_cross_tenant_is_blocked(
    inventory: Inventory,
) -> None:
    with pytest.raises(InventoryConcurrencyScopeError):
        assert_inventory_version(
            inventory,
            tenant_id="tenant-999",
            project_id="project-001",
            expected_version=1,
        )


def test_cross_project_is_blocked(
    inventory: Inventory,
) -> None:
    with pytest.raises(InventoryConcurrencyScopeError):
        assert_inventory_version(
            inventory,
            tenant_id="tenant-001",
            project_id="project-999",
            expected_version=1,
        )


@pytest.mark.parametrize(
    "expected_version",
    [
        0,
        -1,
        True,
        False,
        "1",
        None,
    ],
)
def test_invalid_expected_versions_are_blocked(
    inventory: Inventory,
    expected_version: object,
) -> None:
    with pytest.raises(InventoryInvalidExpectedVersionError):
        assert_inventory_version(
            inventory,
            tenant_id="tenant-001",
            project_id="project-001",
            expected_version=expected_version,  # type: ignore[arg-type]
        )


@pytest.mark.parametrize(
    "operation",
    [
        InventoryConcurrencyOperation.READ,
        InventoryConcurrencyOperation.WRITE,
        InventoryConcurrencyOperation.TRANSITION,
        InventoryConcurrencyOperation.INDEX,
    ],
)
def test_operations_are_recorded(
    inventory: Inventory,
    operation: InventoryConcurrencyOperation,
) -> None:
    receipt = assert_inventory_version(
        inventory,
        tenant_id="tenant-001",
        project_id="project-001",
        expected_version=1,
        operation=operation,
    )

    assert receipt.operation is operation


def test_receipt_serializes_canonically(
    inventory: Inventory,
) -> None:
    receipt = assert_inventory_version(
        inventory,
        tenant_id="tenant-001",
        project_id="project-001",
        expected_version=1,
    )

    data = receipt.to_dict()

    assert data["inventory_id"] == inventory.inventory_id
    assert data["tenant_id"] == "tenant-001"
    assert data["project_id"] == "project-001"
    assert data["operation"] == "WRITE"
    assert data["expected_version"] == 1
    assert data["current_version"] == 1
    assert data["is_current"] is True


def test_guard_does_not_mutate_inventory(
    inventory: Inventory,
) -> None:
    before = inventory.to_dict()

    assert_inventory_version(
        inventory,
        tenant_id="tenant-001",
        project_id="project-001",
        expected_version=inventory.version,
    )

    assert inventory.to_dict() == before


def test_lifecycle_change_invalidates_old_version(
    inventory: Inventory,
) -> None:
    onboarding, _ = inventory.transition(
        "ONBOARDING",
        tenant_id="tenant-001",
        project_id="project-001",
    )

    with pytest.raises(InventoryStaleWriteError):
        assert_inventory_version(
            onboarding,
            tenant_id="tenant-001",
            project_id="project-001",
            expected_version=1,
        )

    receipt = assert_inventory_version(
        onboarding,
        tenant_id="tenant-001",
        project_id="project-001",
        expected_version=2,
    )

    assert receipt.current_version == 2


def test_availability_change_invalidates_old_version(
    inventory: Inventory,
) -> None:
    updated, _ = inventory.set_availability(
        InventoryAvailability.RESERVED,
        tenant_id="tenant-001",
        project_id="project-001",
    )

    with pytest.raises(InventoryStaleWriteError):
        assert_inventory_version(
            updated,
            tenant_id="tenant-001",
            project_id="project-001",
            expected_version=1,
        )

    receipt = assert_inventory_version(
        updated,
        tenant_id="tenant-001",
        project_id="project-001",
        expected_version=2,
    )

    assert receipt.current_version == 2


def test_two_competing_writers_cannot_both_use_same_version(
    inventory: Inventory,
) -> None:
    first_writer = InventoryConcurrencyGuard()

    first_receipt = first_writer.assert_current(
        inventory,
        tenant_id="tenant-001",
        project_id="project-001",
        expected_version=1,
    )

    updated, _ = inventory.touch(
        tenant_id="tenant-001",
        project_id="project-001",
    )

    assert first_receipt.current_version == 1

    with pytest.raises(InventoryStaleWriteError):
        assert_inventory_version(
            updated,
            tenant_id="tenant-001",
            project_id="project-001",
            expected_version=1,
        )


def test_concurrency_error_hierarchy_is_stable(
    inventory: Inventory,
) -> None:
    with pytest.raises(Exception) as error:
        assert_inventory_version(
            inventory,
            tenant_id="tenant-001",
            project_id="project-001",
            expected_version=0,
        )

    assert isinstance(
        error.value,
        InventoryInvalidExpectedVersionError,
    )


def test_operation_can_be_provided_as_string(
    inventory: Inventory,
) -> None:
    receipt = assert_inventory_version(
        inventory,
        tenant_id="tenant-001",
        project_id="project-001",
        expected_version=1,
        operation="INDEX",
    )

    assert receipt.operation is InventoryConcurrencyOperation.INDEX


def test_inventory_identity_remains_authoritative(
    inventory: Inventory,
) -> None:
    receipt = assert_inventory_version(
        inventory,
        tenant_id=inventory.tenant_id,
        project_id=inventory.project_id,
        expected_version=inventory.version,
    )

    assert receipt.inventory_id == inventory.inventory_id
    assert receipt.tenant_id == inventory.tenant_id
    assert receipt.project_id == inventory.project_id