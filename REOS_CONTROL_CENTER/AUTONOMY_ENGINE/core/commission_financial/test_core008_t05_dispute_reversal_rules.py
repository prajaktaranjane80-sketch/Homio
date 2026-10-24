
from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone

import pytest

from .commission_dispute import (
    CommissionDispute,
    CommissionDisputeResolution,
    CommissionDisputeState,
    CommissionDisputeType,
    CommissionDisputeValidationError,
)
from .commission_dispute_conflict import (
    CommissionDisputeConflictError,
    assert_no_conflict,
)
from .commission_dispute_history import (
    CommissionDisputeHistory,
    CommissionDisputeHistoryError,
)
from .commission_dispute_integrity import inspect_integrity
from .commission_dispute_snapshot import CommissionDisputeSnapshot


NOW = datetime(2026, 10, 24, 12, 0, tzinfo=timezone.utc)


def _dispute(**overrides) -> CommissionDispute:
    values = {
        "dispute_id": "dispute-001",
        "tenant_id": "tenant-a",
        "commission_id": "commission-001",
        "settlement_id": "settlement-001",
        "reconciliation_id": None,
        "dispute_version": 1,
        "dispute_type": CommissionDisputeType.AMOUNT,
        "claimant_reference": "broker-001",
        "disputed_amount": None,
        "reason_code": "AMOUNT_MISMATCH",
        "description": "Documented commission amount dispute.",
        "evidence_reference": "evidence-001",
        "authorization_reference": "opening-auth-001",
        "provenance_reference": "provenance-001",
        "opened_at": NOW,
    }
    values.update(overrides)
    return CommissionDispute(**values)


@pytest.mark.parametrize(
    "resolution",
    [
        CommissionDisputeResolution.ACCEPTED,
        CommissionDisputeResolution.PARTIALLY_ACCEPTED,
        CommissionDisputeResolution.SUPERSEDED,
    ],
)
def test_accepted_resolution_advances_version_immutably(resolution):
    opened = _dispute()
    original_fingerprint = opened.immutable_fingerprint

    resolved = opened.resolve(
        resolution=resolution,
        resolution_reference="resolution-001",
    )

    assert resolved.state is CommissionDisputeState.RESOLVED
    assert resolved.resolution is resolution
    assert resolved.dispute_version == opened.dispute_version + 1
    assert resolved.resolution_reference == "resolution-001"
    assert opened.state is CommissionDisputeState.OPEN
    assert opened.immutable_fingerprint == original_fingerprint
    assert resolved.immutable_fingerprint != original_fingerprint


def test_rejection_requires_rejected_state_and_resolution():
    opened = _dispute()

    rejected = opened.resolve(
        resolution=CommissionDisputeResolution.REJECTED,
        resolution_reference="rejection-001",
        state=CommissionDisputeState.REJECTED,
    )

    assert rejected.state is CommissionDisputeState.REJECTED
    assert rejected.resolution is CommissionDisputeResolution.REJECTED
    assert rejected.resolution_reference == "rejection-001"
    assert rejected.dispute_version == 2


@pytest.mark.parametrize(
    ("state", "resolution", "reference"),
    [
        (
            CommissionDisputeState.OPEN,
            CommissionDisputeResolution.ACCEPTED,
            "resolution-001",
        ),
        (
            CommissionDisputeState.UNDER_REVIEW,
            CommissionDisputeResolution.NONE,
            "resolution-001",
        ),
        (
            CommissionDisputeState.RESOLVED,
            CommissionDisputeResolution.NONE,
            None,
        ),
        (
            CommissionDisputeState.RESOLVED,
            CommissionDisputeResolution.REJECTED,
            "resolution-001",
        ),
        (
            CommissionDisputeState.REJECTED,
            CommissionDisputeResolution.ACCEPTED,
            "resolution-001",
        ),
        (
            CommissionDisputeState.WITHDRAWN,
            CommissionDisputeResolution.ACCEPTED,
            "resolution-001",
        ),
    ],
)
def test_inconsistent_state_resolution_pairs_are_rejected(
    state,
    resolution,
    reference,
):
    with pytest.raises(CommissionDisputeValidationError):
        _dispute(
            state=state,
            resolution=resolution,
            resolution_reference=reference,
        )


@pytest.mark.parametrize(
    "terminal",
    [
        CommissionDisputeState.RESOLVED,
        CommissionDisputeState.REJECTED,
        CommissionDisputeState.WITHDRAWN,
    ],
)
def test_terminal_disputes_cannot_be_resolved_again(terminal):
    if terminal is CommissionDisputeState.RESOLVED:
        dispute = _dispute().resolve(
            resolution=CommissionDisputeResolution.ACCEPTED,
            resolution_reference="resolution-001",
        )
    elif terminal is CommissionDisputeState.REJECTED:
        dispute = _dispute().resolve(
            resolution=CommissionDisputeResolution.REJECTED,
            resolution_reference="rejection-001",
            state=CommissionDisputeState.REJECTED,
        )
    else:
        dispute = _dispute(state=CommissionDisputeState.WITHDRAWN)

    with pytest.raises(
        CommissionDisputeValidationError,
        match="terminal disputes cannot be resolved again",
    ):
        dispute.resolve(
            resolution=CommissionDisputeResolution.ACCEPTED,
            resolution_reference="second-resolution-001",
        )


@pytest.mark.parametrize(
    ("state", "resolution"),
    [
        (
            CommissionDisputeState.RESOLVED,
            CommissionDisputeResolution.REJECTED,
        ),
        (
            CommissionDisputeState.REJECTED,
            CommissionDisputeResolution.ACCEPTED,
        ),
        (
            CommissionDisputeState.WITHDRAWN,
            CommissionDisputeResolution.ACCEPTED,
        ),
    ],
)
def test_resolve_rejects_invalid_target_state_pairs(state, resolution):
    with pytest.raises(CommissionDisputeValidationError):
        _dispute().resolve(
            resolution=resolution,
            resolution_reference="resolution-001",
            state=state,
        )


def test_dispute_history_accepts_sequential_versions_and_idempotent_replay():
    opened = _dispute()
    history = CommissionDisputeHistory().append(opened)

    # Re-observing the exact same version/fingerprint is idempotent.
    assert history.append(opened) is history

    resolved = opened.resolve(
        resolution=CommissionDisputeResolution.ACCEPTED,
        resolution_reference="resolution-001",
    )
    updated = history.append(resolved)

    assert len(updated.entries) == 2
    assert updated.latest is not None
    assert updated.latest.dispute_version == 2
    assert updated.latest.state == CommissionDisputeState.RESOLVED.value


def test_dispute_history_rejects_version_gaps():
    opened = _dispute()
    history = CommissionDisputeHistory().append(opened)

    version_three = replace(
        opened.resolve(
            resolution=CommissionDisputeResolution.ACCEPTED,
            resolution_reference="resolution-001",
        ),
        dispute_version=3,
    )

    with pytest.raises(
        CommissionDisputeHistoryError,
        match="versions must advance sequentially",
    ):
        history.append(version_three)


def test_dispute_history_rejects_identity_changes():
    opened = _dispute()
    history = CommissionDisputeHistory().append(opened)

    different_identity = replace(
        opened,
        dispute_id="dispute-999",
    )

    with pytest.raises(
        CommissionDisputeHistoryError,
        match="identity mismatch",
    ):
        history.append(different_identity)


def test_same_version_conflicting_financial_content_is_rejected():
    original = _dispute()
    altered = replace(
        original,
        description="Altered content under the same identity/version.",
    )

    assert original.identity_key == altered.identity_key
    assert original.immutable_fingerprint != altered.immutable_fingerprint

    with pytest.raises(CommissionDisputeConflictError):
        assert_no_conflict(original, altered)


def test_dispute_snapshot_detects_payload_tampering():
    dispute = _dispute()
    snapshot = CommissionDisputeSnapshot.from_dispute(dispute)

    assert snapshot.verify() is True
    assert inspect_integrity(dispute, snapshot).valid is True

    # The frozen wrapper must not let payload mutation pass fingerprint checks.
    snapshot.canonical_payload["reason_code"] = "FORGED_REASON"

    assert snapshot.verify() is False
    report = inspect_integrity(dispute, snapshot)
    assert report.valid is False
    assert "snapshot fingerprint is invalid" in report.reasons
