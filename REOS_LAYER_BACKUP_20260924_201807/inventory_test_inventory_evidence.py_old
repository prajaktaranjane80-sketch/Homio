from __future__ import annotations

import pytest

from AUTONOMY_ENGINE.core.inventory import Inventory, InventoryType
from AUTONOMY_ENGINE.core.inventory_evidence import (
    InventoryEvidence,
    InventoryEvidenceError,
    InventoryEvidenceScopeError,
    InventoryEvidenceStatus,
    InventoryEvidenceType,
)


@pytest.fixture
def evidence() -> InventoryEvidence:
    return InventoryEvidence.register(
        inventory_id="inventory-001",
        tenant_id="tenant-001",
        project_id="project-001",
        inventory_version=1,
        evidence_type=InventoryEvidenceType.OWNERSHIP_DOCUMENT,
        reference="evidence://inventory-001/title-deed-001",
        submitted_by="user-001",
        at="2026-08-30T10:00:00+00:00",
    )


def test_evidence_starts_registered(
    evidence: InventoryEvidence,
) -> None:
    assert evidence.status is InventoryEvidenceStatus.REGISTERED
    assert evidence.version == 1
    assert evidence.inventory_version == 1


def test_evidence_scope_is_enforced(
    evidence: InventoryEvidence,
) -> None:
    evidence.assert_scope(
        tenant_id="tenant-001",
        project_id="project-001",
        inventory_id="inventory-001",
    )


def test_cross_tenant_evidence_scope_is_blocked(
    evidence: InventoryEvidence,
) -> None:
    with pytest.raises(InventoryEvidenceScopeError):
        evidence.assert_scope(
            tenant_id="tenant-999",
            project_id="project-001",
            inventory_id="inventory-001",
        )


def test_cross_project_evidence_scope_is_blocked(
    evidence: InventoryEvidence,
) -> None:
    with pytest.raises(InventoryEvidenceScopeError):
        evidence.assert_scope(
            tenant_id="tenant-001",
            project_id="project-999",
            inventory_id="inventory-001",
        )


def test_cross_inventory_evidence_scope_is_blocked(
    evidence: InventoryEvidence,
) -> None:
    with pytest.raises(InventoryEvidenceScopeError):
        evidence.assert_scope(
            tenant_id="tenant-001",
            project_id="project-001",
            inventory_id="inventory-999",
        )


def test_evidence_status_change_is_immutable(
    evidence: InventoryEvidence,
) -> None:
    updated, event = evidence.with_status(
        InventoryEvidenceStatus.VERIFIED,
        tenant_id="tenant-001",
        project_id="project-001",
        inventory_id="inventory-001",
        at="2026-08-30T10:01:00+00:00",
    )

    assert evidence.status is InventoryEvidenceStatus.REGISTERED
    assert evidence.version == 1

    assert updated.status is InventoryEvidenceStatus.VERIFIED
    assert updated.version == 2
    assert event.status is InventoryEvidenceStatus.VERIFIED


def test_evidence_event_serializes(
    evidence: InventoryEvidence,
) -> None:
    updated, event = evidence.with_status(
        InventoryEvidenceStatus.VERIFIED,
        tenant_id="tenant-001",
        project_id="project-001",
        inventory_id="inventory-001",
    )

    data = event.to_dict()

    assert data["event_type"] == "INVENTORY_EVIDENCE_STATUS_CHANGED"
    assert data["evidence_id"] == evidence.evidence_id
    assert data["inventory_version"] == 1
    assert data["status"] == "VERIFIED"
    assert updated.version == 2


def test_evidence_serializes_canonically(
    evidence: InventoryEvidence,
) -> None:
    data = evidence.to_dict()

    assert data["evidence_id"] == evidence.evidence_id
    assert data["inventory_id"] == "inventory-001"
    assert data["tenant_id"] == "tenant-001"
    assert data["project_id"] == "project-001"
    assert data["inventory_version"] == 1
    assert data["evidence_type"] == "OWNERSHIP_DOCUMENT"
    assert data["status"] == "REGISTERED"
    assert data["source_of_truth"] == "inventory_evidence"


@pytest.mark.parametrize(
    "field_name",
    ["inventory_id", "tenant_id", "project_id", "reference", "submitted_by"],
)
def test_required_evidence_fields_are_enforced(
    field_name: str,
) -> None:
    values = {
        "inventory_id": "inventory-001",
        "tenant_id": "tenant-001",
        "project_id": "project-001",
        "inventory_version": 1,
        "evidence_type": InventoryEvidenceType.OTHER,
        "reference": "evidence://reference",
        "submitted_by": "user-001",
    }

    values[field_name] = ""

    with pytest.raises(InventoryEvidenceError):
        InventoryEvidence.register(**values)