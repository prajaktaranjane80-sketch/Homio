from __future__ import annotations

import pytest

from AUTONOMY_ENGINE.core.inventory import (
    Inventory,
    InventoryType,
)
from AUTONOMY_ENGINE.core.inventory_indexing import (
    InventoryIndexDocument,
    InventoryIndexDocumentError,
    InventoryIndexOperation,
    InventoryIndexScopeError,
    InventoryIndexStaleVersionError,
    InventoryIndexingHook,
    build_inventory_index,
    build_inventory_index_delete,
)


@pytest.fixture
def inventory() -> Inventory:
    return Inventory.create(
        tenant_id="tenant-001",
        project_id="project-001",
        inventory_code="UNIT-001",
        inventory_type=InventoryType.RESIDENTIAL_UNIT,
        name="Unit 001",
        metadata={"floor": 2, "area_sqft": 1200},
        at="2026-08-30T10:00:00+00:00",
    )


@pytest.fixture
def hook() -> InventoryIndexingHook:
    return InventoryIndexingHook()


def test_build_upsert_returns_index_document(
    inventory: Inventory,
    hook: InventoryIndexingHook,
) -> None:
    document = hook.build_upsert(
        inventory,
        tenant_id="tenant-001",
        project_id="project-001",
    )

    assert isinstance(document, InventoryIndexDocument)
    assert document.operation is InventoryIndexOperation.UPSERT


def test_index_uses_canonical_inventory_identity(
    inventory: Inventory,
    hook: InventoryIndexingHook,
) -> None:
    document = hook.build_upsert(
        inventory,
        tenant_id="tenant-001",
        project_id="project-001",
    )

    assert document.index_key == inventory.identity_key
    assert document.inventory_id == inventory.inventory_id
    assert document.tenant_id == inventory.tenant_id
    assert document.project_id == inventory.project_id


def test_index_contains_canonical_inventory_state(
    inventory: Inventory,
    hook: InventoryIndexingHook,
) -> None:
    document = hook.build_upsert(
        inventory,
        tenant_id="tenant-001",
        project_id="project-001",
    )

    assert document.inventory_code == "UNIT-001"
    assert document.inventory_type == "RESIDENTIAL_UNIT"
    assert document.name == "Unit 001"
    assert document.lifecycle == "DRAFT"
    assert document.availability == "AVAILABLE"
    assert document.inventory_version == 1


def test_index_contains_metadata_projection(
    inventory: Inventory,
    hook: InventoryIndexingHook,
) -> None:
    document = hook.build_upsert(
        inventory,
        tenant_id="tenant-001",
        project_id="project-001",
    )

    assert document.payload["metadata"] == {
        "floor": 2,
        "area_sqft": 1200,
    }


def test_cross_tenant_indexing_is_blocked(
    inventory: Inventory,
    hook: InventoryIndexingHook,
) -> None:
    with pytest.raises(InventoryIndexScopeError):
        hook.build_upsert(
            inventory,
            tenant_id="tenant-999",
            project_id="project-001",
        )


def test_cross_project_indexing_is_blocked(
    inventory: Inventory,
    hook: InventoryIndexingHook,
) -> None:
    with pytest.raises(InventoryIndexScopeError):
        hook.build_upsert(
            inventory,
            tenant_id="tenant-001",
            project_id="project-999",
        )


def test_stale_version_is_blocked(
    inventory: Inventory,
    hook: InventoryIndexingHook,
) -> None:
    with pytest.raises(InventoryIndexStaleVersionError):
        hook.build_upsert(
            inventory,
            tenant_id="tenant-001",
            project_id="project-001",
            expected_version=2,
        )


def test_matching_version_is_accepted(
    inventory: Inventory,
    hook: InventoryIndexingHook,
) -> None:
    document = hook.build_upsert(
        inventory,
        tenant_id="tenant-001",
        project_id="project-001",
        expected_version=1,
    )

    assert document.inventory_version == 1


def test_delete_projection_has_delete_operation(
    inventory: Inventory,
    hook: InventoryIndexingHook,
) -> None:
    document = hook.build_delete(
        inventory,
        tenant_id="tenant-001",
        project_id="project-001",
    )

    assert document.operation is InventoryIndexOperation.DELETE
    assert document.index_key == inventory.identity_key


def test_delete_projection_contains_identity(
    inventory: Inventory,
    hook: InventoryIndexingHook,
) -> None:
    document = hook.build_delete(
        inventory,
        tenant_id="tenant-001",
        project_id="project-001",
    )

    assert document.payload["inventory_id"] == inventory.inventory_id
    assert document.payload["tenant_id"] == "tenant-001"
    assert document.payload["project_id"] == "project-001"
    assert document.payload["identity_key"] == inventory.identity_key


def test_document_serializes_canonically(
    inventory: Inventory,
    hook: InventoryIndexingHook,
) -> None:
    document = hook.build_upsert(
        inventory,
        tenant_id="tenant-001",
        project_id="project-001",
    )

    data = document.to_dict()

    assert data["index_key"] == inventory.identity_key
    assert data["inventory_id"] == inventory.inventory_id
    assert data["tenant_id"] == "tenant-001"
    assert data["project_id"] == "project-001"
    assert data["inventory_version"] == 1
    assert data["operation"] == "UPSERT"
    assert data["payload"]["index_name"] == "reos_inventory"


def test_convenience_upsert_api(
    inventory: Inventory,
) -> None:
    document = build_inventory_index(
        inventory,
        tenant_id="tenant-001",
        project_id="project-001",
    )

    assert document.operation is InventoryIndexOperation.UPSERT
    assert document.index_key == inventory.identity_key


def test_convenience_delete_api(
    inventory: Inventory,
) -> None:
    document = build_inventory_index_delete(
        inventory,
        tenant_id="tenant-001",
        project_id="project-001",
    )

    assert document.operation is InventoryIndexOperation.DELETE
    assert document.index_key == inventory.identity_key


def test_indexing_does_not_mutate_inventory(
    inventory: Inventory,
    hook: InventoryIndexingHook,
) -> None:
    before = inventory.to_dict()

    hook.build_upsert(
        inventory,
        tenant_id="tenant-001",
        project_id="project-001",
    )

    assert inventory.to_dict() == before


def test_index_projection_is_deterministic_for_same_inventory(
    inventory: Inventory,
    hook: InventoryIndexingHook,
) -> None:
    first = hook.build_upsert(
        inventory,
        tenant_id="tenant-001",
        project_id="project-001",
    )

    second = hook.build_upsert(
        inventory,
        tenant_id="tenant-001",
        project_id="project-001",
    )

    assert first.to_dict() == second.to_dict()


def test_invalid_expected_version_is_rejected(
    inventory: Inventory,
    hook: InventoryIndexingHook,
) -> None:
    with pytest.raises(InventoryIndexStaleVersionError):
        hook.build_upsert(
            inventory,
            tenant_id="tenant-001",
            project_id="project-001",
            expected_version=0,
        )


def test_document_rejects_invalid_version() -> None:
    with pytest.raises(InventoryIndexDocumentError):
        InventoryIndexDocument(
            index_key="tenant-001:project-001:UNIT-001",
            inventory_id="inventory-001",
            tenant_id="tenant-001",
            project_id="project-001",
            inventory_code="UNIT-001",
            inventory_type="RESIDENTIAL_UNIT",
            name="Unit 001",
            lifecycle="DRAFT",
            availability="AVAILABLE",
            inventory_version=0,
            operation=InventoryIndexOperation.UPSERT,
            payload={},
        )


def test_index_name_is_stable(
    inventory: Inventory,
    hook: InventoryIndexingHook,
) -> None:
    document = hook.build_upsert(
        inventory,
        tenant_id="tenant-001",
        project_id="project-001",
    )

    assert document.payload["index_name"] == "reos_inventory"


def test_updated_inventory_version_is_indexed(
    inventory: Inventory,
    hook: InventoryIndexingHook,
) -> None:
    updated, _ = inventory.touch(
        tenant_id="tenant-001",
        project_id="project-001",
        at="2026-08-30T10:01:00+00:00",
    )

    document = hook.build_upsert(
        updated,
        tenant_id="tenant-001",
        project_id="project-001",
        expected_version=2,
    )

    assert document.inventory_version == 2
    assert document.payload["inventory_version"] == 2


def test_updated_inventory_availability_is_indexed(
    inventory: Inventory,
    hook: InventoryIndexingHook,
) -> None:
    from AUTONOMY_ENGINE.core.inventory import InventoryAvailability

    updated, _ = inventory.set_availability(
        InventoryAvailability.RESERVED,
        tenant_id="tenant-001",
        project_id="project-001",
    )

    document = hook.build_upsert(
        updated,
        tenant_id="tenant-001",
        project_id="project-001",
    )

    assert document.availability == "RESERVED"
    assert document.payload["availability"] == "RESERVED"


def test_updated_inventory_lifecycle_is_indexed(
    inventory: Inventory,
    hook: InventoryIndexingHook,
) -> None:
    from AUTONOMY_ENGINE.core.inventory import InventoryLifecycle

    updated, _ = inventory.transition(
        InventoryLifecycle.ONBOARDING,
        tenant_id="tenant-001",
        project_id="project-001",
    )

    document = hook.build_upsert(
        updated,
        tenant_id="tenant-001",
        project_id="project-001",
    )

    assert document.lifecycle == "ONBOARDING"
    assert document.payload["lifecycle"] == "ONBOARDING"