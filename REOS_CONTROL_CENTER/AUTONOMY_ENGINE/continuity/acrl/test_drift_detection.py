"""ACRL T10 — Drift Detection tests."""

from __future__ import annotations

import pytest

from AUTONOMY_ENGINE.continuity.acrl.drift_detection import (
    DriftAuthorityError,
    DriftDetectionEngine,
    DriftDetectionError,
    DriftIntegrityError,
    DriftSeverity,
    DriftType,
    DriftValidationError,
    create_drift_baseline,
    detect_drift,
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


def test_baseline_can_be_created() -> None:
    baseline = create_drift_baseline(
        make_components()
    )

    assert baseline.authority == (
        "REOS_CONTROL_CENTER"
    )


def test_baseline_contains_all_components() -> None:
    baseline = create_drift_baseline(
        make_components()
    )

    assert set(
        baseline.component_fingerprints
    ) == set(
        DriftDetectionEngine.COMPONENTS
    )


def test_baseline_is_deterministic() -> None:
    components = make_components()

    first = create_drift_baseline(
        components
    )
    second = create_drift_baseline(
        components
    )

    assert (
        first.overall_fingerprint
        == second.overall_fingerprint
    )


def test_identical_state_has_no_drift() -> None:
    components = make_components()
    baseline = create_drift_baseline(
        components
    )

    report = detect_drift(
        baseline,
        components,
    )

    assert report.drift_detected is False
    assert report.severity == DriftSeverity.NONE
    assert report.fail_closed is False
    assert report.findings == ()


def test_execution_drift_is_detected() -> None:
    baseline = create_drift_baseline(
        make_components()
    )

    current = make_components()
    current["execution"][
        "current_subtask"
    ] = "CORE-005-T02"

    report = detect_drift(
        baseline,
        current,
    )

    assert report.drift_detected is True
    assert report.severity == DriftSeverity.MEDIUM

    assert any(
        finding.drift_type
        == DriftType.EXECUTION
        for finding in report.findings
    )


def test_gate_drift_is_detected() -> None:
    baseline = create_drift_baseline(
        make_components()
    )

    current = make_components()
    current["gate_continuity"][
        "current_gate"
    ] = "CORE-006"

    report = detect_drift(
        baseline,
        current,
    )

    assert report.drift_detected is True
    assert report.severity == DriftSeverity.MEDIUM


def test_architecture_drift_is_critical() -> None:
    baseline = create_drift_baseline(
        make_components()
    )

    current = make_components()
    current["architecture"][
        "status"
    ] = "UNLOCKED"

    report = detect_drift(
        baseline,
        current,
    )

    assert report.drift_detected is True
    assert report.severity == DriftSeverity.CRITICAL
    assert report.fail_closed is True


def test_architecture_drift_fails_closed() -> None:
    baseline = create_drift_baseline(
        make_components()
    )

    current = make_components()
    current["architecture"][
        "version"
    ] = "2.0"

    with pytest.raises(
        DriftDetectionError
    ):
        DriftDetectionEngine.detect_or_raise(
            baseline,
            current,
        )


def test_dependency_drift_is_high() -> None:
    baseline = create_drift_baseline(
        make_components()
    )

    current = make_components()
    current["dependency_authority"][
        "authority"
    ] = "UNKNOWN"

    report = detect_drift(
        baseline,
        current,
    )

    assert report.severity == DriftSeverity.HIGH
    assert report.fail_closed is True


def test_checkpoint_drift_is_low() -> None:
    baseline = create_drift_baseline(
        make_components()
    )

    current = make_components()
    current["checkpoint"][
        "status"
    ] = "CHANGED"

    report = detect_drift(
        baseline,
        current,
    )

    assert report.severity == DriftSeverity.LOW
    assert report.fail_closed is False


def test_missing_component_is_rejected() -> None:
    baseline = create_drift_baseline(
        make_components()
    )

    current = make_components()
    del current["checkpoint"]

    with pytest.raises(
        DriftAuthorityError
    ):
        detect_drift(
            baseline,
            current,
        )


def test_invalid_baseline_input_is_rejected() -> None:
    with pytest.raises(
        DriftValidationError
    ):
        DriftDetectionEngine.create_baseline(
            "invalid"
        )


def test_missing_baseline_component_is_rejected() -> None:
    components = make_components()
    del components["architecture"]

    with pytest.raises(
        DriftAuthorityError
    ):
        create_drift_baseline(
            components
        )


def test_invalid_component_is_rejected() -> None:
    components = make_components()
    components["execution"] = "invalid"

    with pytest.raises(
        DriftAuthorityError
    ):
        create_drift_baseline(
            components
        )


def test_baseline_tampering_is_detected() -> None:
    baseline = create_drift_baseline(
        make_components()
    )

    altered = dict(
        baseline.components
    )

    altered["execution"] = {
        "current_gate": "CORE-999"
    }

    object.__setattr__(
        baseline,
        "components",
        altered,
    )

    with pytest.raises(
        DriftIntegrityError
    ):
        DriftDetectionEngine.verify_baseline(
            baseline
        )


def test_report_is_machine_readable() -> None:
    components = make_components()
    baseline = create_drift_baseline(
        components
    )

    report = detect_drift(
        baseline,
        components,
    )

    data = report.to_dict()

    assert data["verified"] if "verified" in data else True
    assert data["drift_detected"] is False
    assert data["severity"] == "NONE"


def test_fingerprint_is_deterministic() -> None:
    value = {
        "b": 2,
        "a": 1,
    }

    first = DriftDetectionEngine.fingerprint(
        value
    )

    second = DriftDetectionEngine.fingerprint(
        {
            "a": 1,
            "b": 2,
        }
    )

    assert first == second


def test_fingerprint_has_sha256_length() -> None:
    fingerprint = (
        DriftDetectionEngine.fingerprint(
            {"test": "value"}
        )
    )

    assert len(fingerprint) == 64


def test_multiple_drifts_use_highest_severity() -> None:
    baseline = create_drift_baseline(
        make_components()
    )

    current = make_components()

    current["architecture"][
        "version"
    ] = "2.0"

    current["checkpoint"][
        "status"
    ] = "CHANGED"

    report = detect_drift(
        baseline,
        current,
    )

    assert report.severity == DriftSeverity.CRITICAL
    assert len(report.findings) == 2


def test_drift_type_mapping_is_complete() -> None:
    assert set(
        DriftDetectionEngine.TYPE_MAP
    ) == set(
        DriftDetectionEngine.COMPONENTS
    )


def test_report_preserves_baseline_fingerprint() -> None:
    components = make_components()
    baseline = create_drift_baseline(
        components
    )

    report = detect_drift(
        baseline,
        components,
    )

    assert (
        report.baseline_fingerprint
        == baseline.overall_fingerprint
    )


def test_current_fingerprint_changes_after_drift() -> None:
    baseline = create_drift_baseline(
        make_components()
    )

    current = make_components()

    first = detect_drift(
        baseline,
        current,
    )

    current["execution"][
        "current_subtask"
    ] = "CORE-005-T02"

    second = detect_drift(
        baseline,
        current,
    )

    assert (
        first.current_fingerprint
        != second.current_fingerprint
    )