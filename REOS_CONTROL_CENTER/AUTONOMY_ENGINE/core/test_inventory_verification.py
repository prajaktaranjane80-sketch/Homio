from __future__ import annotations

import pytest

from AUTONOMY_ENGINE.core.inventory import (
    Inventory,
    InventoryType,
)
from AUTONOMY_ENGINE.core.inventory_verification import (
    InventoryVerification,
    InventoryVerificationError,
    InventoryVerificationRequirementError,
    InventoryVerificationState,
    InventoryVerificationTransitionError,
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


@pytest.fixture
def verification(inventory: Inventory) -> InventoryVerification:
    return InventoryVerification.for_inventory(
        inventory,
        at="2026-08-30T10:00:00+00:00",
    )


def test_verification_starts_unverified(
    verification: InventoryVerification,
) -> None:
    assert verification.state is InventoryVerificationState.UNVERIFIED
    assert verification.version == 1
    assert verification.verified_by is None
    assert verification.reason is None


def test_verification_links_to_canonical_inventory(
    inventory: Inventory,
    verification: InventoryVerification,
) -> None:
    assert verification.inventory_id == inventory.inventory_id
    assert verification.tenant_id == inventory.tenant_id
    assert verification.project_id == inventory.project_id
    assert verification.inventory_version == inventory.version


def test_unverified_can_move_to_pending(
    inventory: Inventory,
    verification: InventoryVerification,
) -> None:
    updated, event = verification.transition(
        inventory,
        InventoryVerificationState.PENDING,
        tenant_id="tenant-001",
        project_id="project-001",
        at="2026-08-30T10:01:00+00:00",
    )

    assert updated.state is InventoryVerificationState.PENDING
    assert updated.version == 2
    assert event.event_type == "INVENTORY_VERIFICATION_CHANGED"
    assert event.inventory_id == inventory.inventory_id
    assert event.verification_state is InventoryVerificationState.PENDING


@pytest.mark.parametrize(
    "target",
    [
        InventoryVerificationState.VERIFIED,
        InventoryVerificationState.REJECTED,
    ],
)
def test_unverified_cannot_skip_pending(
    inventory: Inventory,
    verification: InventoryVerification,
    target: InventoryVerificationState,
) -> None:
    with pytest.raises(InventoryVerificationTransitionError):
        verification.transition(
            inventory,
            target,
            tenant_id="tenant-001",
            project_id="project-001",
        )


def test_pending_can_be_verified(
    inventory: Inventory,
    verification: InventoryVerification,
) -> None:
    pending, _ = verification.transition(
        inventory,
        InventoryVerificationState.PENDING,
        tenant_id="tenant-001",
        project_id="project-001",
        at="2026-08-30T10:01:00+00:00",
    )

    verified, event = pending.transition(
        inventory,
        InventoryVerificationState.VERIFIED,
        tenant_id="tenant-001",
        project_id="project-001",
        verified_by="user-001",
        at="2026-08-30T10:02:00+00:00",
    )

    assert verified.state is InventoryVerificationState.VERIFIED
    assert verified.verified_by == "user-001"
    assert verified.reason is None
    assert verified.version == 3
    assert event.verification_state is InventoryVerificationState.VERIFIED


def test_verified_requires_verified_by(
    inventory: Inventory,
    verification: InventoryVerification,
) -> None:
    pending, _ = verification.transition(
        inventory,
        InventoryVerificationState.PENDING,
        tenant_id="tenant-001",
        project_id="project-001",
    )

    with pytest.raises(InventoryVerificationRequirementError):
        pending.transition(
            inventory,
            InventoryVerificationState.VERIFIED,
            tenant_id="tenant-001",
            project_id="project-001",
        )


def test_pending_can_be_rejected(
    inventory: Inventory,
    verification: InventoryVerification,
) -> None:
    pending, _ = verification.transition(
        inventory,
        InventoryVerificationState.PENDING,
        tenant_id="tenant-001",
        project_id="project-001",
    )

    rejected, event = pending.transition(
        inventory,
        InventoryVerificationState.REJECTED,
        tenant_id="tenant-001",
        project_id="project-001",
        reason="Ownership document mismatch",
    )

    assert rejected.state is InventoryVerificationState.REJECTED
    assert rejected.reason == "Ownership document mismatch"
    assert rejected.verified_by is None
    assert event.payload["from"] == "PENDING"
    assert event.payload["to"] == "REJECTED"


def test_rejection_requires_reason(
    inventory: Inventory,
    verification: InventoryVerification,
) -> None:
    pending, _ = verification.transition(
        inventory,
        InventoryVerificationState.PENDING,
        tenant_id="tenant-001",
        project_id="project-001",
    )

    with pytest.raises(InventoryVerificationRequirementError):
        pending.transition(
            inventory,
            InventoryVerificationState.REJECTED,
            tenant_id="tenant-001",
            project_id="project-001",
        )


@pytest.mark.parametrize(
    "current_state",
    [
        InventoryVerificationState.VERIFIED,
        InventoryVerificationState.REJECTED,
    ],
)
def test_terminal_verification_states_can_return_to_pending(
    inventory: Inventory,
    verification: InventoryVerification,
    current_state: InventoryVerificationState,
) -> None:
    pending, _ = verification.transition(
        inventory,
        InventoryVerificationState.PENDING,
        tenant_id="tenant-001",
        project_id="project-001",
    )

    if current_state is InventoryVerificationState.VERIFIED:
        current, _ = pending.transition(
            inventory,
            current_state,
            tenant_id="tenant-001",
            project_id="project-001",
            verified_by="user-001",
        )
    else:
        current, _ = pending.transition(
            inventory,
            current_state,
            tenant_id="tenant-001",
            project_id="project-001",
            reason="Rejected for re-verification",
        )

    updated, _ = current.transition(
        inventory,
        InventoryVerificationState.PENDING,
        tenant_id="tenant-001",
        project_id="project-001",
    )

    assert updated.state is InventoryVerificationState.PENDING
    assert updated.version == current.version + 1


def test_cross_tenant_verification_is_blocked(
    inventory: Inventory,
    verification: InventoryVerification,
) -> None:
    with pytest.raises(InventoryVerificationError):
        verification.transition(
            inventory,
            InventoryVerificationState.PENDING,
            tenant_id="tenant-999",
            project_id="project-001",
        )


def test_cross_project_verification_is_blocked(
    inventory: Inventory,
    verification: InventoryVerification,
) -> None:
    with pytest.raises(InventoryVerificationError):
        verification.transition(
            inventory,
            InventoryVerificationState.PENDING,
            tenant_id="tenant-001",
            project_id="project-999",
        )


def test_stale_inventory_version_is_blocked(
    inventory: Inventory,
    verification: InventoryVerification,
) -> None:
    updated_inventory, _ = inventory.touch(
        tenant_id="tenant-001",
        project_id="project-001",
        at="2026-08-30T10:01:00+00:00",
    )

    with pytest.raises(InventoryVerificationError):
        verification.transition(
            updated_inventory,
            InventoryVerificationState.PENDING,
            tenant_id="tenant-001",
            project_id="project-001",
        )


def test_verification_is_immutable(
    inventory: Inventory,
    verification: InventoryVerification,
) -> None:
    updated, _ = verification.transition(
        inventory,
        InventoryVerificationState.PENDING,
        tenant_id="tenant-001",
        project_id="project-001",
    )

    assert verification.state is InventoryVerificationState.UNVERIFIED
    assert verification.version == 1
    assert updated.state is InventoryVerificationState.PENDING
    assert updated.version == 2


def test_verification_serializes_canonically(
    inventory: Inventory,
    verification: InventoryVerification,
) -> None:
    pending, _ = verification.transition(
        inventory,
        InventoryVerificationState.PENDING,
        tenant_id="tenant-001",
        project_id="project-001",
    )

    data = pending.to_dict()

    assert data["verification_id"] == verification.verification_id
    assert data["inventory_id"] == inventory.inventory_id
    assert data["tenant_id"] == "tenant-001"
    assert data["project_id"] == "project-001"
    assert data["inventory_version"] == inventory.version
    assert data["state"] == "PENDING"
    assert data["version"] == 2


def test_verification_event_serializes_canonically(
    inventory: Inventory,
    verification: InventoryVerification,
) -> None:
    _, event = verification.transition(
        inventory,
        InventoryVerificationState.PENDING,
        tenant_id="tenant-001",
        project_id="project-001",
    )

    data = event.to_dict()

    assert data["event_type"] == "INVENTORY_VERIFICATION_CHANGED"
    assert data["inventory_id"] == inventory.inventory_id
    assert data["tenant_id"] == "tenant-001"
    assert data["project_id"] == "project-001"
    assert data["inventory_version"] == inventory.version
    assert data["verification_state"] == "PENDING"


def test_inventory_domain_remains_unchanged(
    inventory: Inventory,
) -> None:
    assert inventory.version == 1
    assert inventory.lifecycle.value == "DRAFT"
    assert inventory.availability.value == "AVAILABLE"
    assert inventory.source_of_truth == "inventory"