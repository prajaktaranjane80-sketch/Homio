from __future__ import annotations

import pytest

from AUTONOMY_ENGINE.core.inventory import (
    Inventory,
    InventoryAvailability,
    InventoryType,
)
from AUTONOMY_ENGINE.core.inventory_consistency import (
    InventoryConsistencyIdentityError,
    InventoryConsistencyProjectionError,
    InventoryConsistencyScopeError,
    InventoryConsistencyValidator,
    InventoryConsistencyVersionError,
    validate_inventory_consistency,
)
from AUTONOMY_ENGINE.core.inventory_indexing import (
    InventoryIndexingHook,
)
from AUTONOMY_ENGINE.core.inventory_verification import (
    InventoryVerification,
)


@pytest.fixture
def inventory() -> Inventory:
    return Inventory.create(
        tenant_id="tenant-001",
        project_id="project-001",
        inventory_code="UNIT-001",
        inventory_type=InventoryType.RESIDENTIAL_UNIT,
        name="Unit 001",
        metadata={"area_sqft": 1200},
        at="2026-08-30T10:00:00+00:00",
    )


@pytest.fixture
def validator() -> InventoryConsistencyValidator:
    return InventoryConsistencyValidator()


def test_valid_inventory_passes(
    inventory: Inventory,
    validator: InventoryConsistencyValidator,
) -> None:
    result = validator.validate_inventory(
        inventory,
        tenant_id="tenant-001",
        project_id="project-001",
    )

    assert result.valid is True
    assert result.violations == ()


def test_convenience_validation_passes(
    inventory: Inventory,
) -> None:
    result = validate_inventory_consistency(
        inventory,
        tenant_id="tenant-001",
        project_id="project-001",
    )

    assert result.valid is True


def test_cross_tenant_consistency_is_blocked(
    inventory: Inventory,
    validator: InventoryConsistencyValidator,
) -> None:
    with pytest.raises(InventoryConsistencyScopeError):
        validator.assert_inventory(
            inventory,
            tenant_id="tenant-999",
            project_id="project-001",
        )


def test_cross_project_consistency_is_blocked(
    inventory: Inventory,
    validator: InventoryConsistencyValidator,
) -> None:
    with pytest.raises(InventoryConsistencyScopeError):
        validator.assert_inventory(
            inventory,
            tenant_id="tenant-001",
            project_id="project-999",
        )


def test_identity_key_is_consistent(
    inventory: Inventory,
    validator: InventoryConsistencyValidator,
) -> None:
    result = validator.validate_inventory(
        inventory,
        tenant_id="tenant-001",
        project_id="project-001",
    )

    assert result.valid is True
    assert inventory.identity_key == (
        "tenant-001:project-001:UNIT-001"
    )


def test_inventory_version_is_valid(
    inventory: Inventory,
    validator: InventoryConsistencyValidator,
) -> None:
    result = validator.validate_inventory(
        inventory,
        tenant_id="tenant-001",
        project_id="project-001",
    )

    assert result.valid is True
    assert inventory.version == 1


def test_lifecycle_is_part_of_consistency_boundary(
    inventory: Inventory,
    validator: InventoryConsistencyValidator,
) -> None:
    result = validator.validate_inventory(
        inventory,
        tenant_id="tenant-001",
        project_id="project-001",
    )

    assert result.valid is True
    assert inventory.lifecycle.value == "DRAFT"


def test_availability_is_part_of_consistency_boundary(
    inventory: Inventory,
    validator: InventoryConsistencyValidator,
) -> None:
    result = validator.validate_inventory(
        inventory,
        tenant_id="tenant-001",
        project_id="project-001",
    )

    assert result.valid is True
    assert inventory.availability is InventoryAvailability.AVAILABLE


def test_inventory_event_matches_inventory(
    inventory: Inventory,
    validator: InventoryConsistencyValidator,
) -> None:
    updated, event = inventory.touch(
        tenant_id="tenant-001",
        project_id="project-001",
        at="2026-08-30T10:01:00+00:00",
    )

    result = validator.validate_event(updated, event)

    assert result.valid is True
    assert result.violations == ()


def test_cross_tenant_event_is_blocked(
    inventory: Inventory,
    validator: InventoryConsistencyValidator,
) -> None:
    _, event = inventory.touch(
        tenant_id="tenant-001",
        project_id="project-001",
    )

    tampered_event = type(event)(
        event_id=event.event_id,
        event_type=event.event_type,
        inventory_id=event.inventory_id,
        project_id=event.project_id,
        tenant_id="tenant-999",
        inventory_version=event.inventory_version,
        occurred_at=event.occurred_at,
        payload=event.payload,
    )

    with pytest.raises(InventoryConsistencyScopeError):
        validator.assert_event(inventory, tampered_event)


def test_cross_project_event_is_blocked(
    inventory: Inventory,
    validator: InventoryConsistencyValidator,
) -> None:
    _, event = inventory.touch(
        tenant_id="tenant-001",
        project_id="project-001",
    )

    tampered_event = type(event)(
        event_id=event.event_id,
        event_type=event.event_type,
        inventory_id=event.inventory_id,
        project_id="project-999",
        tenant_id=event.tenant_id,
        inventory_version=event.inventory_version,
        occurred_at=event.occurred_at,
        payload=event.payload,
    )

    with pytest.raises(InventoryConsistencyScopeError):
        validator.assert_event(inventory, tampered_event)


def test_stale_event_version_is_blocked(
    inventory: Inventory,
    validator: InventoryConsistencyValidator,
) -> None:
    _, event = inventory.touch(
        tenant_id="tenant-001",
        project_id="project-001",
    )

    with pytest.raises(InventoryConsistencyVersionError):
        validator.assert_event(inventory, event)


def test_verification_matches_inventory(
    inventory: Inventory,
    validator: InventoryConsistencyValidator,
) -> None:
    verification = InventoryVerification.for_inventory(inventory)

    result = validator.validate_verification(
        inventory,
        verification,
    )

    assert result.valid is True


def test_cross_tenant_verification_is_blocked(
    inventory: Inventory,
    validator: InventoryConsistencyValidator,
) -> None:
    verification = InventoryVerification.for_inventory(inventory)

    tampered = type(verification)(
        verification_id=verification.verification_id,
        inventory_id=verification.inventory_id,
        tenant_id="tenant-999",
        project_id=verification.project_id,
        inventory_version=verification.inventory_version,
        state=verification.state,
        verified_by=verification.verified_by,
        reason=verification.reason,
        created_at=verification.created_at,
        updated_at=verification.updated_at,
        version=verification.version,
    )

    with pytest.raises(InventoryConsistencyScopeError):
        validator.assert_verification(inventory, tampered)


def test_cross_project_verification_is_blocked(
    inventory: Inventory,
    validator: InventoryConsistencyValidator,
) -> None:
    verification = InventoryVerification.for_inventory(inventory)

    tampered = type(verification)(
        verification_id=verification.verification_id,
        inventory_id=verification.inventory_id,
        tenant_id=verification.tenant_id,
        project_id="project-999",
        inventory_version=verification.inventory_version,
        state=verification.state,
        verified_by=verification.verified_by,
        reason=verification.reason,
        created_at=verification.created_at,
        updated_at=verification.updated_at,
        version=verification.version,
    )

    with pytest.raises(InventoryConsistencyScopeError):
        validator.assert_verification(inventory, tampered)


def test_stale_verification_version_is_blocked(
    inventory: Inventory,
    validator: InventoryConsistencyValidator,
) -> None:
    verification = InventoryVerification.for_inventory(inventory)

    updated, _ = inventory.touch(
        tenant_id="tenant-001",
        project_id="project-001",
    )

    with pytest.raises(InventoryConsistencyVersionError):
        validator.assert_verification(updated, verification)


def test_index_matches_inventory(
    inventory: Inventory,
    validator: InventoryConsistencyValidator,
) -> None:
    document = InventoryIndexingHook().build_upsert(
        inventory,
        tenant_id="tenant-001",
        project_id="project-001",
    )

    result = validator.validate_index(
        inventory,
        document,
    )

    assert result.valid is True


def test_cross_tenant_index_is_blocked(
    inventory: Inventory,
    validator: InventoryConsistencyValidator,
) -> None:
    document = InventoryIndexingHook().build_upsert(
        inventory,
        tenant_id="tenant-001",
        project_id="project-001",
    )

    tampered = type(document)(
        index_key=document.index_key,
        inventory_id=document.inventory_id,
        tenant_id="tenant-999",
        project_id=document.project_id,
        inventory_code=document.inventory_code,
        inventory_type=document.inventory_type,
        name=document.name,
        lifecycle=document.lifecycle,
        availability=document.availability,
        inventory_version=document.inventory_version,
        operation=document.operation,
        payload=document.payload,
    )

    with pytest.raises(InventoryConsistencyScopeError):
        validator.assert_index(inventory, tampered)


def test_cross_project_index_is_blocked(
    inventory: Inventory,
    validator: InventoryConsistencyValidator,
) -> None:
    document = InventoryIndexingHook().build_upsert(
        inventory,
        tenant_id="tenant-001",
        project_id="project-001",
    )

    tampered = type(document)(
        index_key=document.index_key,
        inventory_id=document.inventory_id,
        tenant_id=document.tenant_id,
        project_id="project-999",
        inventory_code=document.inventory_code,
        inventory_type=document.inventory_type,
        name=document.name,
        lifecycle=document.lifecycle,
        availability=document.availability,
        inventory_version=document.inventory_version,
        operation=document.operation,
        payload=document.payload,
    )

    with pytest.raises(InventoryConsistencyScopeError):
        validator.assert_index(inventory, tampered)


def test_stale_index_version_is_blocked(
    inventory: Inventory,
    validator: InventoryConsistencyValidator,
) -> None:
    document = InventoryIndexingHook().build_upsert(
        inventory,
        tenant_id="tenant-001",
        project_id="project-001",
    )

    updated, _ = inventory.touch(
        tenant_id="tenant-001",
        project_id="project-001",
    )

    with pytest.raises(InventoryConsistencyVersionError):
        validator.assert_index(updated, document)


def test_index_identity_mismatch_is_blocked(
    inventory: Inventory,
    validator: InventoryConsistencyValidator,
) -> None:
    document = InventoryIndexingHook().build_upsert(
        inventory,
        tenant_id="tenant-001",
        project_id="project-001",
    )

    tampered = type(document)(
        index_key="wrong:key",
        inventory_id=document.inventory_id,
        tenant_id=document.tenant_id,
        project_id=document.project_id,
        inventory_code=document.inventory_code,
        inventory_type=document.inventory_type,
        name=document.name,
        lifecycle=document.lifecycle,
        availability=document.availability,
        inventory_version=document.inventory_version,
        operation=document.operation,
        payload=document.payload,
    )

    with pytest.raises(InventoryConsistencyIdentityError):
        validator.assert_index(inventory, tampered)


def test_index_lifecycle_mismatch_is_blocked(
    inventory: Inventory,
    validator: InventoryConsistencyValidator,
) -> None:
    document = InventoryIndexingHook().build_upsert(
        inventory,
        tenant_id="tenant-001",
        project_id="project-001",
    )

    tampered = type(document)(
        index_key=document.index_key,
        inventory_id=document.inventory_id,
        tenant_id=document.tenant_id,
        project_id=document.project_id,
        inventory_code=document.inventory_code,
        inventory_type=document.inventory_type,
        name=document.name,
        lifecycle="ACTIVE",
        availability=document.availability,
        inventory_version=document.inventory_version,
        operation=document.operation,
        payload=document.payload,
    )

    with pytest.raises(InventoryConsistencyProjectionError):
        validator.assert_index(inventory, tampered)


def test_index_availability_mismatch_is_blocked(
    inventory: Inventory,
    validator: InventoryConsistencyValidator,
) -> None:
    document = InventoryIndexingHook().build_upsert(
        inventory,
        tenant_id="tenant-001",
        project_id="project-001",
    )

    tampered = type(document)(
        index_key=document.index_key,
        inventory_id=document.inventory_id,
        tenant_id=document.tenant_id,
        project_id=document.project_id,
        inventory_code=document.inventory_code,
        inventory_type=document.inventory_type,
        name=document.name,
        lifecycle=document.lifecycle,
        availability="SOLD",
        inventory_version=document.inventory_version,
        operation=document.operation,
        payload=document.payload,
    )

    with pytest.raises(InventoryConsistencyProjectionError):
        validator.assert_index(inventory, tampered)


def test_consistency_result_serializes(
    inventory: Inventory,
    validator: InventoryConsistencyValidator,
) -> None:
    result = validator.validate_inventory(
        inventory,
        tenant_id="tenant-001",
        project_id="project-001",
    )

    data = result.to_dict()

    assert data["valid"] is True
    assert "TENANT_SCOPE" in data["checked_invariants"]
    assert "PROJECT_SCOPE" in data["checked_invariants"]
    assert "IDENTITY" in data["checked_invariants"]
    assert data["violations"] == []


def test_validator_is_read_only(
    inventory: Inventory,
    validator: InventoryConsistencyValidator,
) -> None:
    before = inventory.to_dict()

    validator.validate_inventory(
        inventory,
        tenant_id="tenant-001",
        project_id="project-001",
    )

    assert inventory.to_dict() == before