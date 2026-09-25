from __future__ import annotations

import pytest

from AUTONOMY_ENGINE.core.inventory import Inventory, InventoryType
from AUTONOMY_ENGINE.core.inventory_evidence import (
    InventoryEvidence,
    InventoryEvidenceType,
)
from AUTONOMY_ENGINE.core.inventory_history import InventoryHistory
from AUTONOMY_ENGINE.core.inventory_history_evidence import (
    InventoryHistoryEvidenceLink,
    InventoryHistoryEvidenceScopeError,
    InventoryHistoryEvidenceVersionError,
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
def history(inventory: Inventory) -> InventoryHistory:
    return InventoryHistory.from_inventory(
        inventory,
        at="2026-08-30T10:01:00+00:00",
    )


@pytest.fixture
def evidence() -> InventoryEvidence:
    return InventoryEvidence.register(
        inventory_id="",
        tenant_id="tenant-001",
        project_id="project-001",
        inventory_version=1,
        evidence_type=InventoryEvidenceType.OWNERSHIP_DOCUMENT,
        reference="evidence://title-deed",
        submitted_by="user-001",
        at="2026-08-30T10:01:00+00:00",
    )


def test_history_and_evidence_can_be_linked(
    history: InventoryHistory,
) -> None:
    evidence = InventoryEvidence.register(
        inventory_id=history.inventory_id,
        tenant_id=history.tenant_id,
        project_id=history.project_id,
        inventory_version=history.inventory_version,
        evidence_type=InventoryEvidenceType.OWNERSHIP_DOCUMENT,
        reference="evidence://title-deed",
        submitted_by="user-001",
        at="2026-08-30T10:01:00+00:00",
    )

    link = InventoryHistoryEvidenceLink.create(
        history,
        evidence,
        at="2026-08-30T10:02:00+00:00",
    )

    assert link.history_id == history.history_id
    assert link.evidence_id == evidence.evidence_id
    assert link.inventory_id == history.inventory_id
    assert link.inventory_version == 1


def test_cross_inventory_link_is_blocked(
    history: InventoryHistory,
) -> None:
    evidence = InventoryEvidence.register(
        inventory_id="different-inventory",
        tenant_id="tenant-001",
        project_id="project-001",
        inventory_version=1,
        evidence_type=InventoryEvidenceType.OTHER,
        reference="evidence://other",
        submitted_by="user-001",
    )

    with pytest.raises(InventoryHistoryEvidenceScopeError):
        InventoryHistoryEvidenceLink.create(
            history,
            evidence,
            at="2026-08-30T10:02:00+00:00",
        )


def test_cross_tenant_link_is_blocked(
    history: InventoryHistory,
) -> None:
    evidence = InventoryEvidence.register(
        inventory_id=history.inventory_id,
        tenant_id="tenant-999",
        project_id=history.project_id,
        inventory_version=1,
        evidence_type=InventoryEvidenceType.OTHER,
        reference="evidence://other",
        submitted_by="user-001",
    )

    with pytest.raises(InventoryHistoryEvidenceScopeError):
        InventoryHistoryEvidenceLink.create(
            history,
            evidence,
            at="2026-08-30T10:02:00+00:00",
        )


def test_cross_project_link_is_blocked(
    history: InventoryHistory,
) -> None:
    evidence = InventoryEvidence.register(
        inventory_id=history.inventory_id,
        tenant_id=history.tenant_id,
        project_id="project-999",
        inventory_version=1,
        evidence_type=InventoryEvidenceType.OTHER,
        reference="evidence://other",
        submitted_by="user-001",
    )

    with pytest.raises(InventoryHistoryEvidenceScopeError):
        InventoryHistoryEvidenceLink.create(
            history,
            evidence,
            at="2026-08-30T10:02:00+00:00",
        )


def test_version_mismatch_is_blocked(
    history: InventoryHistory,
) -> None:
    evidence = InventoryEvidence.register(
        inventory_id=history.inventory_id,
        tenant_id=history.tenant_id,
        project_id=history.project_id,
        inventory_version=2,
        evidence_type=InventoryEvidenceType.OTHER,
        reference="evidence://future-version",
        submitted_by="user-001",
    )

    with pytest.raises(InventoryHistoryEvidenceVersionError):
        InventoryHistoryEvidenceLink.create(
            history,
            evidence,
            at="2026-08-30T10:02:00+00:00",
        )


def test_link_serializes_canonically(
    history: InventoryHistory,
) -> None:
    evidence = InventoryEvidence.register(
        inventory_id=history.inventory_id,
        tenant_id=history.tenant_id,
        project_id=history.project_id,
        inventory_version=history.inventory_version,
        evidence_type=InventoryEvidenceType.OTHER,
        reference="evidence://test",
        submitted_by="user-001",
    )

    link = InventoryHistoryEvidenceLink.create(
        history,
        evidence,
        at="2026-08-30T10:02:00+00:00",
    )

    data = link.to_dict()

    assert data["link_id"] == link.link_id
    assert data["history_id"] == history.history_id
    assert data["evidence_id"] == evidence.evidence_id
    assert data["inventory_id"] == history.inventory_id
    assert data["tenant_id"] == "tenant-001"
    assert data["project_id"] == "project-001"
    assert data["inventory_version"] == 1