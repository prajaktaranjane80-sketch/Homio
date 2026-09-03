"""ACRL T09 — State Integrity / Fingerprint tests."""

from __future__ import annotations

import pytest

from AUTONOMY_ENGINE.continuity.acrl.state_integrity import (
    ComponentFingerprint,
    StateIntegrityAuthorityError,
    StateIntegrityEngine,
    StateIntegrityFingerprintError,
    StateIntegritySnapshot,
    StateIntegrityTamperError,
    StateIntegrityValidationError,
    build_state_integrity,
    verify_state_integrity,
)


def make_components() -> dict[str, dict[str, object]]:
    return {
        "project_identity": {
            "project": "HOMIO / REOS",
            "authority": "REOS_CONTROL_CENTER",
        },
        "architecture": {
            "status": "LOCKED",
            "version": "1.0",
        },
        "execution": {
            "current_gate": "CORE-005",
            "current_subtask": "CORE-005-T01",
            "status": "CONTROL_CENTER_DRIVEN",
        },
        "gate_continuity": {
            "current_gate": "CORE-005",
            "current_subtask": "CORE-005-T01",
        },
        "dependency_authority": {
            "authority": "REOS_CONTROL_CENTER",
            "status": "VALID",
        },
        "checkpoint": {
            "checkpoint_id": "CP-T09-001",
            "status": "VALID",
        },
    }


def test_build_returns_snapshot() -> None:
    snapshot = build_state_integrity(
        make_components()
    )

    assert isinstance(
        snapshot,
        StateIntegritySnapshot,
    )


def test_authority_is_control_center() -> None:
    snapshot = build_state_integrity(
        make_components()
    )

    assert (
        snapshot.authority
        == "REOS_CONTROL_CENTER"
    )


def test_schema_version_is_present() -> None:
    snapshot = build_state_integrity(
        make_components()
    )

    assert snapshot.schema_version == "1.0"


def test_sha256_is_used() -> None:
    snapshot = build_state_integrity(
        make_components()
    )

    assert snapshot.algorithm == "sha256"


def test_all_required_components_are_fingerprinted() -> None:
    snapshot = build_state_integrity(
        make_components()
    )

    names = {
        item.name
        for item in snapshot.component_fingerprints
    }

    assert names == set(
        StateIntegrityEngine.REQUIRED_COMPONENTS
    )


def test_component_fingerprint_is_deterministic() -> None:
    components = make_components()

    first = build_state_integrity(
        components
    )

    second = build_state_integrity(
        components
    )

    assert (
        first.overall_fingerprint
        == second.overall_fingerprint
    )


def test_mapping_order_does_not_change_fingerprint() -> None:
    first = {
        "a": 1,
        "b": 2,
    }

    second = {
        "b": 2,
        "a": 1,
    }

    assert (
        StateIntegrityEngine.fingerprint(first)
        == StateIntegrityEngine.fingerprint(second)
    )


def test_identical_state_verifies() -> None:
    components = make_components()

    snapshot = build_state_integrity(
        components
    )

    report = verify_state_integrity(
        snapshot,
        components,
    )

    assert report.verified is True
    assert report.tampered_components == ()
    assert report.missing_components == ()


def test_changed_component_is_detected() -> None:
    components = make_components()

    snapshot = build_state_integrity(
        components
    )

    changed = make_components()

    changed["execution"][
        "current_subtask"
    ] = "CORE-005-T02"

    report = verify_state_integrity(
        snapshot,
        changed,
    )

    assert report.verified is False
    assert "execution" in (
        report.tampered_components
    )


def test_changed_component_fails_closed() -> None:
    components = make_components()

    snapshot = build_state_integrity(
        components
    )

    changed = make_components()

    changed["execution"][
        "current_subtask"
    ] = "CORE-005-T02"

    with pytest.raises(
        StateIntegrityTamperError
    ):
        StateIntegrityEngine.verify_or_raise(
            snapshot,
            changed,
        )


def test_missing_component_is_detected() -> None:
    components = make_components()

    snapshot = build_state_integrity(
        components
    )

    current = make_components()
    del current["checkpoint"]

    report = verify_state_integrity(
        snapshot,
        current,
    )

    assert report.verified is False
    assert "checkpoint" in (
        report.missing_components
    )


def test_missing_component_fails_closed() -> None:
    components = make_components()

    snapshot = build_state_integrity(
        components
    )

    current = make_components()
    del current["checkpoint"]

    with pytest.raises(
        StateIntegrityAuthorityError
    ):
        StateIntegrityEngine.verify_or_raise(
            snapshot,
            current,
        )


def test_missing_required_component_during_build_is_rejected() -> None:
    components = make_components()
    del components["architecture"]

    with pytest.raises(
        StateIntegrityAuthorityError
    ):
        build_state_integrity(
            components
        )


def test_invalid_input_is_rejected() -> None:
    with pytest.raises(
        StateIntegrityValidationError
    ):
        build_state_integrity(
            "invalid"
        )


def test_invalid_component_is_rejected() -> None:
    components = make_components()
    components["checkpoint"] = "invalid"

    with pytest.raises(
        StateIntegrityAuthorityError
    ):
        build_state_integrity(
            components
        )


def test_compare_identical_states() -> None:
    first = make_components()
    second = make_components()

    assert (
        StateIntegrityEngine.compare(
            first,
            second,
        )
        is True
    )


def test_compare_different_states() -> None:
    first = make_components()
    second = make_components()

    second["checkpoint"][
        "status"
    ] = "CHANGED"

    assert (
        StateIntegrityEngine.compare(
            first,
            second,
        )
        is False
    )


def test_report_is_machine_readable() -> None:
    snapshot = build_state_integrity(
        make_components()
    )

    report = verify_state_integrity(
        snapshot,
        make_components(),
    )

    data = report.to_dict()

    assert data["verified"] is True
    assert (
        data["authority"]
        == "REOS_CONTROL_CENTER"
    )


def test_snapshot_is_machine_readable() -> None:
    snapshot = build_state_integrity(
        make_components()
    )

    data = snapshot.to_dict()

    assert (
        data["overall_fingerprint"]
        == snapshot.overall_fingerprint
    )

    assert len(
        data["component_fingerprints"]
    ) == len(
        StateIntegrityEngine.REQUIRED_COMPONENTS
    )


def test_component_fingerprint_model() -> None:
    component = ComponentFingerprint(
        name="execution",
        fingerprint="abc123",
    )

    assert component.to_dict() == {
        "name": "execution",
        "fingerprint": "abc123",
        "algorithm": "sha256",
    }


def test_verify_rejects_invalid_snapshot() -> None:
    with pytest.raises(
        StateIntegrityValidationError
    ):
        StateIntegrityEngine.verify(
            object(),
            make_components(),
        )


def test_verify_rejects_invalid_current_state() -> None:
    snapshot = build_state_integrity(
        make_components()
    )

    with pytest.raises(
        StateIntegrityValidationError
    ):
        StateIntegrityEngine.verify(
            snapshot,
            "invalid",
        )


def test_fingerprint_length_is_sha256_length() -> None:
    fingerprint = (
        StateIntegrityEngine.fingerprint(
            {"test": "value"}
        )
    )

    assert len(fingerprint) == 64


def test_verify_or_raise_returns_report() -> None:
    components = make_components()

    snapshot = build_state_integrity(
        components
    )

    report = StateIntegrityEngine.verify_or_raise(
        snapshot,
        components,
    )

    assert report.verified is True


def test_integrity_snapshot_is_immutable() -> None:
    snapshot = build_state_integrity(
        make_components()
    )

    with pytest.raises(
        AttributeError
    ):
        snapshot.overall_fingerprint = "changed"