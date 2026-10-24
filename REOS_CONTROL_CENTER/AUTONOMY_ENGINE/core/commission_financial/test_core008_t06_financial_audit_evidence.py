from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone
import math

import pytest

from .commission_financial_audit import (
    CommissionFinancialAuditAction,
    CommissionFinancialAuditConflictError,
    CommissionFinancialAuditEntry,
    CommissionFinancialAuditIntegrityError,
    CommissionFinancialAuditOutcome,
    CommissionFinancialAuditTrail,
    CommissionFinancialAuditValidationError,
    CommissionFinancialEvidenceLink,
    assert_financial_audit_trail_integrity,
    inspect_financial_audit_trail,
)

UTC = timezone.utc
T0 = datetime(2026, 10, 24, 10, 0, tzinfo=UTC)


def _evidence(evidence_id: str = "evidence-001") -> CommissionFinancialEvidenceLink:
    return CommissionFinancialEvidenceLink(
        evidence_kind="BANK_CONFIRMATION",
        evidence_id=evidence_id,
        evidence_fingerprint=f"fingerprint-{evidence_id}",
        authority_reference=f"evidence-service:{evidence_id}",
    )


def _entry(**overrides) -> CommissionFinancialAuditEntry:
    values = {
        "audit_id": "audit-001",
        "tenant_id": "tenant-a",
        "commission_id": "commission-001",
        "subject_type": "SETTLEMENT",
        "subject_id": "settlement-001",
        "subject_version": 1,
        "action": CommissionFinancialAuditAction.CREATED,
        "outcome": CommissionFinancialAuditOutcome.SUCCEEDED,
        "actor_reference": "operator-001",
        "occurred_at": T0,
        "subject_fingerprint": "subject-fingerprint-001",
        "provenance_reference": "provenance-001",
        "after_fingerprint": "after-fingerprint-001",
        "metadata": {"source": "test", "details": {"codes": ["A", "B"]}},
    }
    values.update(overrides)
    return CommissionFinancialAuditEntry(**values)


def test_audit_entry_fingerprint_and_nested_metadata_are_immutable():
    nested = {"codes": ["A", "B"]}
    entry = _entry(metadata={"details": nested})
    before = entry.immutable_fingerprint

    nested["codes"].append("CHANGED")
    assert entry.immutable_fingerprint == before
    assert entry.to_dict()["metadata"] == {"details": {"codes": ["A", "B"]}}

    with pytest.raises(TypeError):
        entry.metadata["details"]["other"] = "blocked"
    with pytest.raises(AttributeError):
        entry.metadata["details"]["codes"].append("blocked")


def test_critical_actions_require_authorization_reference():
    with pytest.raises(
        CommissionFinancialAuditValidationError,
        match="require authorization_reference",
    ):
        _entry(
            action=CommissionFinancialAuditAction.REVERSED,
            authorization_reference=None,
            evidence_links=(_evidence(),),
        )


def test_failed_critical_attempt_can_be_recorded_without_authorization():
    entry = _entry(
        action=CommissionFinancialAuditAction.REVERSED,
        outcome=CommissionFinancialAuditOutcome.FAILED,
        authorization_reference=None,
        evidence_links=(),
        after_fingerprint=None,
    )
    assert entry.authorization_reference is None
    assert entry.outcome is CommissionFinancialAuditOutcome.FAILED


def test_successful_reversal_requires_evidence_and_after_fingerprint():
    with pytest.raises(
        CommissionFinancialAuditValidationError,
        match="require evidence links",
    ):
        _entry(
            action=CommissionFinancialAuditAction.REVERSED,
            authorization_reference="approval-001",
            evidence_links=(),
        )

    with pytest.raises(
        CommissionFinancialAuditValidationError,
        match="require after_fingerprint",
    ):
        _entry(
            action=CommissionFinancialAuditAction.REVERSED,
            authorization_reference="approval-001",
            evidence_links=(_evidence(),),
            after_fingerprint=None,
        )


def test_created_audit_entry_cannot_claim_a_before_fingerprint():
    with pytest.raises(
        CommissionFinancialAuditValidationError,
        match="cannot have before_fingerprint",
    ):
        _entry(before_fingerprint="pretend-previous-state")


def test_duplicate_evidence_link_identity_is_rejected():
    with pytest.raises(
        CommissionFinancialAuditValidationError,
        match="iterable of evidence references",
    ):
        _entry(evidence_links=None)

    link = _evidence()
    with pytest.raises(
        CommissionFinancialAuditValidationError,
        match="Duplicate evidence link identity",
    ):
        _entry(evidence_links=(link, link))


def test_audit_entry_rejects_naive_datetime_and_boolean_version():
    with pytest.raises(
        CommissionFinancialAuditValidationError,
        match="timezone-aware",
    ):
        _entry(occurred_at=datetime(2026, 10, 24, 10, 0))

    with pytest.raises(
        CommissionFinancialAuditValidationError,
        match="positive integer",
    ):
        _entry(subject_version=True)


def test_audit_entry_rejects_unsupported_metadata_values():
    with pytest.raises(
        CommissionFinancialAuditValidationError,
        match="supported deterministic values",
    ):
        _entry(metadata={"unsafe": {1, 2, 3}})

    with pytest.raises(
        CommissionFinancialAuditValidationError,
        match="supported deterministic values",
    ):
        _entry(metadata={"unsafe": math.nan})


def test_audit_trail_appends_sequential_tamper_evident_records():
    first = _entry()
    trail = CommissionFinancialAuditTrail(
        "tenant-a",
        "commission-001",
    ).append(first)

    second = _entry(
        audit_id="audit-002",
        action=CommissionFinancialAuditAction.UPDATED,
        occurred_at=T0 + timedelta(seconds=1),
        subject_version=2,
        before_fingerprint="before-002",
        after_fingerprint="after-002",
        subject_fingerprint="subject-fingerprint-002",
    )
    trail = trail.append(second)

    assert [record.sequence for record in trail.records] == [1, 2]
    assert trail.records[0].previous_record_fingerprint is None
    assert (
        trail.records[1].previous_record_fingerprint
        == trail.records[0].record_fingerprint
    )
    assert trail.latest is trail.records[-1]
    assert trail.chain_fingerprint == trail.records[-1].record_fingerprint
    assert trail.verify_integrity() is True
    assert inspect_financial_audit_trail(trail).valid is True
    assert_financial_audit_trail_integrity(trail)


def test_exact_replay_is_idempotent_and_does_not_grow_chain():
    entry = _entry()
    trail = CommissionFinancialAuditTrail(
        "tenant-a",
        "commission-001",
    ).append(entry)

    replayed = trail.append(entry)
    assert replayed is trail
    assert len(replayed.records) == 1


def test_same_audit_id_with_different_payload_is_conflict():
    entry = _entry()
    trail = CommissionFinancialAuditTrail(
        "tenant-a",
        "commission-001",
    ).append(entry)
    conflict = replace(
        entry,
        subject_fingerprint="forged-fingerprint",
    )

    with pytest.raises(
        CommissionFinancialAuditConflictError,
        match="conflicts",
    ):
        trail.append(conflict)


def test_audit_trail_is_tenant_and_commission_scoped():
    trail = CommissionFinancialAuditTrail("tenant-a", "commission-001")

    with pytest.raises(
        CommissionFinancialAuditValidationError,
        match="does not match trail",
    ):
        trail.append(_entry(tenant_id="tenant-b"))

    with pytest.raises(
        CommissionFinancialAuditValidationError,
        match="crossed tenant scope",
    ):
        _entry().assert_tenant("tenant-b")


def test_audit_trail_rejects_out_of_order_events():
    trail = CommissionFinancialAuditTrail(
        "tenant-a",
        "commission-001",
    ).append(_entry())

    older = _entry(
        audit_id="audit-000",
        occurred_at=T0 - timedelta(seconds=1),
        subject_version=2,
        before_fingerprint="before",
        after_fingerprint="after",
        action=CommissionFinancialAuditAction.UPDATED,
    )

    with pytest.raises(
        CommissionFinancialAuditValidationError,
        match="nondecreasing occurred_at",
    ):
        trail.append(older)


def test_tampering_with_earlier_entry_breaks_following_chain_link():
    first = _entry()
    trail = CommissionFinancialAuditTrail(
        "tenant-a",
        "commission-001",
    ).append(first)

    second = _entry(
        audit_id="audit-002",
        action=CommissionFinancialAuditAction.UPDATED,
        occurred_at=T0 + timedelta(seconds=1),
        subject_version=2,
        before_fingerprint="before-002",
        after_fingerprint="after-002",
        subject_fingerprint="subject-fingerprint-002",
    )
    trail = trail.append(second)

    altered_first = replace(
        trail.records[0].entry,
        subject_fingerprint="tampered",
    )
    altered_record = replace(
        trail.records[0],
        entry=altered_first,
    )
    tampered_trail = replace(
        trail,
        records=(altered_record, trail.records[1]),
    )

    report = inspect_financial_audit_trail(tampered_trail)
    assert report.valid is False
    assert "record fingerprint is invalid" in report.reason

    with pytest.raises(CommissionFinancialAuditIntegrityError):
        assert_financial_audit_trail_integrity(tampered_trail)


def test_tampering_with_the_latest_entry_is_detected_without_a_following_record():
    trail = CommissionFinancialAuditTrail(
        "tenant-a",
        "commission-001",
    ).append(_entry())

    altered_entry = replace(
        trail.records[0].entry,
        subject_fingerprint="tampered-latest",
    )
    altered_record = replace(
        trail.records[0],
        entry=altered_entry,
    )
    tampered_trail = replace(
        trail,
        records=(altered_record,),
    )

    report = inspect_financial_audit_trail(tampered_trail)
    assert report.valid is False
    assert "record fingerprint is invalid" in report.reason


def test_sequence_gap_and_previous_link_tampering_are_detected():
    trail = CommissionFinancialAuditTrail(
        "tenant-a",
        "commission-001",
    ).append(_entry())

    trail = trail.append(
        _entry(
            audit_id="audit-002",
            action=CommissionFinancialAuditAction.UPDATED,
            occurred_at=T0 + timedelta(seconds=1),
            subject_version=2,
            before_fingerprint="before",
            after_fingerprint="after",
        )
    )

    bad_first = replace(
        trail.records[0],
        sequence=2,
    )
    bad_sequence = replace(
        trail,
        records=(bad_first, trail.records[1]),
    )
    report = inspect_financial_audit_trail(bad_sequence)
    assert report.valid is False
    assert "sequence gap" in report.reason

    bad_second = replace(
        trail.records[1],
        previous_record_fingerprint="forged-link",
    )
    bad_link = replace(
        trail,
        records=(trail.records[0], bad_second),
    )
    report = inspect_financial_audit_trail(bad_link)
    assert report.valid is False
    assert "previous-record fingerprint link" in report.reason


def test_find_and_serialization_expose_references_not_evidence_payloads():
    link = _evidence("statement-001")
    entry = _entry(
        action=CommissionFinancialAuditAction.RECONCILED,
        authorization_reference="approval-001",
        evidence_links=(link,),
    )
    trail = CommissionFinancialAuditTrail(
        "tenant-a",
        "commission-001",
    ).append(entry)

    found = trail.find("audit-001")
    assert found is trail.records[0]

    serialized = trail.to_dict()
    assert serialized["entry_count"] == 1
    assert (
        serialized["records"][0]["entry"]["evidence_links"][0]["evidence_id"]
        == "statement-001"
    )
    assert "payload" not in serialized["records"][0]["entry"]["evidence_links"][0]
    assert trail.find("missing") is None
