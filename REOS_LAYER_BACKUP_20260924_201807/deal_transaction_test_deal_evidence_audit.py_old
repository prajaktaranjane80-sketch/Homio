from __future__ import annotations

import pytest

from .deal import Deal
from .deal_evidence_audit import (
    DealAuditEntry,
    DealAuditConflictError,
    DealEvidenceAuditError,
    DealEvidenceReference,
)



def make_deal() -> Deal:
    return Deal.create(
        tenant_id="tenant-001",
        customer_id="customer-001",
        broker_id="broker-001",
        builder_id="builder-001",
        project_id="project-001",
        unit_id="unit-001",
        at="2026-09-24T10:00:00+00:00",
    )


def test_evidence_reference_is_immutable() -> None:
    evidence = DealEvidenceReference.create(
        evidence_id="evidence-001",
        deal_id="deal-001",
        tenant_id="tenant-001",
        evidence_type="CUSTOMER_ORIGIN",
        reference="ref://evidence/001",
        created_at="2026-09-24T10:00:00+00:00",
    )

    with pytest.raises(AttributeError):
        evidence.reference = "changed"  # type: ignore[misc]


def test_audit_entry_is_immutable() -> None:
    audit = DealAuditEntry.create(
        audit_id="audit-001",
        deal_id="deal-001",
        tenant_id="tenant-001",
        action="DEAL_CREATED",
        actor_id="user-001",
        created_at="2026-09-24T10:00:00+00:00",
    )

    with pytest.raises(AttributeError):
        audit.action = "CHANGED"  # type: ignore[misc]


def test_evidence_scope_is_tenant_and_deal_bound() -> None:
    evidence = DealEvidenceReference.create(
        evidence_id="evidence-001",
        deal_id="deal-001",
        tenant_id="tenant-001",
        evidence_type="CUSTOMER_ORIGIN",
        reference="ref://001",
    )

    with pytest.raises(DealEvidenceAuditError):
        evidence.assert_scope(
            deal_id="deal-002",
            tenant_id="tenant-001",
        )

    with pytest.raises(DealEvidenceAuditError):
        evidence.assert_scope(
            deal_id="deal-001",
            tenant_id="tenant-002",
        )


def test_audit_scope_is_tenant_and_deal_bound() -> None:
    audit = DealAuditEntry.create(
        audit_id="audit-001",
        deal_id="deal-001",
        tenant_id="tenant-001",
        action="DEAL_CREATED",
        actor_id="user-001",
    )

    with pytest.raises(DealEvidenceAuditError):
        audit.assert_scope(
            deal_id="deal-002",
            tenant_id="tenant-001",
        )

    with pytest.raises(DealEvidenceAuditError):
        audit.assert_scope(
            deal_id="deal-001",
            tenant_id="tenant-002",
        )


def test_evidence_serialization_is_canonical() -> None:
    evidence = DealEvidenceReference.create(
        evidence_id="evidence-001",
        deal_id="deal-001",
        tenant_id="tenant-001",
        evidence_type="CUSTOMER_ORIGIN",
        reference="ref://001",
        created_at="2026-09-24T10:00:00+00:00",
        metadata={"channel": "web"},
    )

    payload = evidence.to_dict()

    assert payload["evidence_id"] == "evidence-001"
    assert payload["deal_id"] == "deal-001"
    assert payload["tenant_id"] == "tenant-001"
    assert payload["source_of_truth"] == "evidence"
    assert payload["metadata"] == {"channel": "web"}


def test_audit_serialization_is_canonical() -> None:
    audit = DealAuditEntry.create(
        audit_id="audit-001",
        deal_id="deal-001",
        tenant_id="tenant-001",
        action="STATUS_CHANGED",
        actor_id="user-001",
        created_at="2026-09-24T10:00:00+00:00",
        details={"from": "DRAFT", "to": "ACTIVE"},
    )

    payload = audit.to_dict()

    assert payload["audit_id"] == "audit-001"
    assert payload["deal_id"] == "deal-001"
    assert payload["tenant_id"] == "tenant-001"
    assert payload["source_of_truth"] == "deal_audit"
    assert payload["details"]["to"] == "ACTIVE"


def test_deal_module_compiles_with_t06_types() -> None:
    deal = make_deal()

    assert deal.deal_id
    assert deal.tenant_id == "tenant-001"
    assert deal.version == 1


def test_deal_serialization_contains_t06_collections() -> None:
    deal = make_deal()
    payload = deal.to_dict()

    assert payload["deal_id"] == deal.deal_id
    assert payload["tenant_id"] == "tenant-001"
    assert payload["source_of_truth"] == "deal"
    assert payload["evidence"] == []
    assert payload["audit_log"] == []

