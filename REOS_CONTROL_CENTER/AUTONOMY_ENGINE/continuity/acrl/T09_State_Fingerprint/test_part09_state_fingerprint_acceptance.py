"""ACRL T09 — PART 09 State Fingerprint acceptance tests."""

from __future__ import annotations

import pytest

from AUTONOMY_ENGINE.continuity.acrl.T09_State_Fingerprint.fingerprint_identity import (
    FingerprintIdentityEngine,
)
from AUTONOMY_ENGINE.continuity.acrl.T09_State_Fingerprint.fingerprint_validation import (
    FingerprintValidationEngine,
)
from AUTONOMY_ENGINE.continuity.acrl.T09_State_Fingerprint.state_integrity import (
    StateIntegrityEngine,
)


def make_state(
    *,
    current_gate: str = "CORE-005",
    current_subtask: str = "CORE-005-T01",
) -> dict[str, object]:
    """Build deterministic reconstructed authoritative state."""
    return {
        "project_identity": {
            "project": "HOMIO / REOS",
            "authority": "REOS_CONTROL_CENTER",
        },
        "architecture": {
            "status": "LOCKED",
            "source": "REOS_ARCHITECTURE",
        },
        "execution": {
            "current_gate": current_gate,
            "current_subtask": current_subtask,
            "status": "CONTROL_CENTER_DRIVEN",
        },
        "gate_continuity": {
            "current_gate": current_gate,
            "current_subtask": current_subtask,
        },
        "dependency_authority": {
            "authority": "REOS_CONTROL_CENTER",
        },
        "checkpoint": {
            "checkpoint_id": "CP-P09-001",
            "resume_mode": "SAFE_AUTONOMOUS_RESUME",
        },
    }


def test_canonical_state_hash_is_deterministic() -> None:
    state = make_state()

    first = StateIntegrityEngine.fingerprint(state)
    second = StateIntegrityEngine.fingerprint(state)

    assert first == second
    assert len(first) == 64


def test_semantic_fingerprint_is_deterministic() -> None:
    state = make_state()

    first = StateIntegrityEngine.fingerprint(state)
    second = StateIntegrityEngine.fingerprint(dict(state))

    assert first == second


def test_state_fingerprint_changes_when_authoritative_state_changes() -> None:
    original = make_state()
    changed = make_state(current_gate="CORE-006")

    original_fingerprint = StateIntegrityEngine.fingerprint(
        original
    )
    changed_fingerprint = StateIntegrityEngine.fingerprint(
        changed
    )

    assert original_fingerprint != changed_fingerprint


def test_state_comparison_identifies_same_state() -> None:
    left = make_state()
    right = make_state()

    assert (
        StateIntegrityEngine.compare(
            left,
            right,
        )
        is True
    )


def test_state_comparison_identifies_changed_state() -> None:
    left = make_state()
    right = make_state(
        current_subtask="CORE-005-T02",
    )

    assert (
        StateIntegrityEngine.compare(
            left,
            right,
        )
        is False
    )


def test_fingerprint_identity_binds_to_state_fingerprint() -> None:
    snapshot = StateIntegrityEngine.build(
        make_state()
    )

    identity = FingerprintIdentityEngine.build(
        snapshot
    )

    assert (
        identity.overall_fingerprint
        == snapshot.overall_fingerprint
    )

    assert (
        FingerprintIdentityEngine.validate(
            identity
        )
        is True
    )


def test_reconstructed_state_matches_canonical_snapshot() -> None:
    canonical = make_state()

    snapshot = StateIntegrityEngine.build(
        canonical
    )

    reconstructed = make_state()

    report = StateIntegrityEngine.verify(
        snapshot,
        reconstructed,
    )

    assert report.verified is True
    assert report.tampered_components == ()
    assert report.missing_components == ()


def test_reconstructed_changed_state_is_detected() -> None:
    canonical = make_state()

    snapshot = StateIntegrityEngine.build(
        canonical
    )

    reconstructed = make_state(
        current_gate="CORE-006",
    )

    report = StateIntegrityEngine.verify(
        snapshot,
        reconstructed,
    )

    assert report.verified is False
    assert "execution" in report.tampered_components


def test_identity_and_snapshot_form_valid_t09_package() -> None:
    snapshot = StateIntegrityEngine.build(
        make_state()
    )

    identity = FingerprintIdentityEngine.build(
        snapshot
    )

    result = (
        FingerprintValidationEngine.validate_or_raise(
            snapshot,
            identity,
        )
    )

    assert result.valid is True


def test_tampered_identity_cannot_validate() -> None:
    snapshot = StateIntegrityEngine.build(
        make_state()
    )

    identity = FingerprintIdentityEngine.build(
        snapshot
    )

    object.__setattr__(
        identity,
        "overall_fingerprint",
        "tampered",
    )

    with pytest.raises(Exception):
        FingerprintValidationEngine.validate_or_raise(
            snapshot,
            identity,
        )
