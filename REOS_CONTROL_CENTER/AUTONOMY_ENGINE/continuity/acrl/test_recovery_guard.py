"""ACRL T11 — Recovery / Fail-Closed Guard tests."""

from __future__ import annotations

import pytest

from AUTONOMY_ENGINE.continuity.acrl.recovery_guard import (
    RecoveryAction,
    RecoveryAuthorityError,
    RecoveryBlockedError,
    RecoveryDecision,
    RecoveryGuard,
    RecoveryIntegrityError,
    RecoveryReason,
    RecoveryReport,
    RecoveryRequest,
    RecoveryValidationError,
    evaluate_recovery,
    validate_recovery,
)


def make_request(
    *,
    failure_type: str = "transient",
    component: str = "execution",
    recoverable: bool = True,
    authoritative: bool = True,
    destructive: bool = False,
    integrity_verified: bool = True,
) -> RecoveryRequest:
    return RecoveryRequest(
        failure_type=failure_type,
        component=component,
        recoverable=recoverable,
        authoritative=authoritative,
        destructive=destructive,
        integrity_verified=integrity_verified,
    )


def test_recovery_request_serializes() -> None:
    request = make_request()

    data = request.to_dict()

    assert data["failure_type"] == "transient"
    assert data["component"] == "execution"
    assert data["recoverable"] is True


def test_transient_failure_is_recoverable() -> None:
    report = evaluate_recovery(
        make_request(
            failure_type="transient"
        )
    )

    assert (
        report.decision
        == RecoveryDecision.RECOVER
    )


def test_timeout_is_recoverable() -> None:
    report = evaluate_recovery(
        make_request(
            failure_type="timeout"
        )
    )

    assert (
        report.decision
        == RecoveryDecision.RECOVER
    )


def test_retryable_failure_is_recoverable() -> None:
    report = evaluate_recovery(
        make_request(
            failure_type="retryable"
        )
    )

    assert (
        report.decision
        == RecoveryDecision.RECOVER
    )


def test_explicit_recoverable_error_is_recoverable() -> None:
    report = evaluate_recovery(
        make_request(
            failure_type="database_error",
            recoverable=True,
        )
    )

    assert (
        report.decision
        == RecoveryDecision.RECOVER
    )


def test_non_recoverable_failure_fails_closed() -> None:
    report = evaluate_recovery(
        make_request(
            failure_type="database_error",
            recoverable=False,
        )
    )

    assert (
        report.decision
        == RecoveryDecision.FAIL_CLOSED
    )
    assert report.fail_closed is True


def test_unknown_failure_fails_closed() -> None:
    report = evaluate_recovery(
        make_request(
            failure_type="unknown"
        )
    )

    assert (
        report.decision
        == RecoveryDecision.FAIL_CLOSED
    )


def test_architecture_drift_fails_closed() -> None:
    report = evaluate_recovery(
        make_request(
            failure_type="architecture_drift"
        )
    )

    assert (
        report.decision
        == RecoveryDecision.FAIL_CLOSED
    )

    assert (
        report.reason
        == RecoveryReason.ARCHITECTURE_DRIFT
    )


def test_authority_conflict_fails_closed() -> None:
    report = evaluate_recovery(
        make_request(
            failure_type="authority_conflict"
        )
    )

    assert (
        report.decision
        == RecoveryDecision.FAIL_CLOSED
    )

    assert (
        report.reason
        == RecoveryReason.AUTHORITY_CONFLICT
    )


def test_integrity_failure_fails_closed() -> None:
    report = evaluate_recovery(
        make_request(
            failure_type="integrity"
        )
    )

    assert (
        report.decision
        == RecoveryDecision.FAIL_CLOSED
    )

    assert (
        report.reason
        == RecoveryReason.INTEGRITY_FAILURE
    )


def test_tamper_failure_fails_closed() -> None:
    report = evaluate_recovery(
        make_request(
            failure_type="tamper"
        )
    )

    assert (
        report.decision
        == RecoveryDecision.FAIL_CLOSED
    )


def test_destructive_action_fails_closed() -> None:
    report = evaluate_recovery(
        make_request(
            destructive=True
        )
    )

    assert (
        report.decision
        == RecoveryDecision.FAIL_CLOSED
    )

    assert (
        report.reason
        == RecoveryReason.DESTRUCTIVE_ACTION
    )


def test_unverified_integrity_is_rejected() -> None:
    with pytest.raises(
        RecoveryIntegrityError
    ):
        evaluate_recovery(
            make_request(
                integrity_verified=False
            )
        )


def test_missing_authority_is_rejected() -> None:
    with pytest.raises(
        RecoveryAuthorityError
    ):
        evaluate_recovery(
            make_request(
                authoritative=False
            )
        )


def test_empty_failure_type_is_rejected() -> None:
    with pytest.raises(
        RecoveryValidationError
    ):
        evaluate_recovery(
            make_request(
                failure_type=""
            )
        )


def test_empty_component_is_rejected() -> None:
    with pytest.raises(
        RecoveryValidationError
    ):
        evaluate_recovery(
            make_request(
                component=""
            )
        )


def test_recovery_action_is_non_destructive() -> None:
    report = evaluate_recovery(
        make_request()
    )

    assert report.action is not None
    assert report.action.destructive is False
    assert report.action.automatic is True


def test_recovery_action_does_not_require_human() -> None:
    report = evaluate_recovery(
        make_request()
    )

    assert report.action is not None
    assert (
        report.action.requires_human
        is False
    )


def test_validate_recovery_accepts_safe_recovery() -> None:
    report = evaluate_recovery(
        make_request()
    )

    assert validate_recovery(
        report
    ) is True


def test_validate_recovery_rejects_fail_closed() -> None:
    report = evaluate_recovery(
        make_request(
            failure_type="architecture_drift"
        )
    )

    assert validate_recovery(
        report
    ) is False


def test_evaluate_or_raise_blocks_unsafe_recovery() -> None:
    request = make_request(
        failure_type="architecture_drift"
    )

    with pytest.raises(
        RecoveryBlockedError
    ):
        RecoveryGuard.evaluate_or_raise(
            request
        )


def test_evaluate_or_raise_allows_safe_recovery() -> None:
    report = RecoveryGuard.evaluate_or_raise(
        make_request()
    )

    assert (
        report.decision
        == RecoveryDecision.RECOVER
    )


def test_fingerprint_is_deterministic() -> None:
    request = make_request()

    first = RecoveryGuard.fingerprint(
        request.to_dict()
    )

    second = RecoveryGuard.fingerprint(
        request.to_dict()
    )

    assert first == second


def test_fingerprint_is_sha256_length() -> None:
    fingerprint = RecoveryGuard.fingerprint(
        {"test": "value"}
    )

    assert len(fingerprint) == 64


def test_report_is_machine_readable() -> None:
    report = evaluate_recovery(
        make_request()
    )

    data = report.to_dict()

    assert data["authority"] == (
        "REOS_CONTROL_CENTER"
    )

    assert data["decision"] == "RECOVER"
    assert data["fail_closed"] is False


def test_report_contains_request_fingerprint() -> None:
    report = evaluate_recovery(
        make_request()
    )

    assert (
        len(report.request_fingerprint)
        == 64
    )


def test_report_is_validated() -> None:
    report = evaluate_recovery(
        make_request()
    )

    assert report.validated is True


def test_recovery_reason_for_transient_failure() -> None:
    report = evaluate_recovery(
        make_request(
            failure_type="timeout"
        )
    )

    assert (
        report.reason
        == RecoveryReason.TRANSIENT_FAILURE
    )


def test_recovery_reason_for_explicit_recovery() -> None:
    report = evaluate_recovery(
        make_request(
            failure_type="custom_failure",
            recoverable=True,
        )
    )

    assert (
        report.reason
        == RecoveryReason.RECOVERABLE_EXECUTION_ERROR
    )


def test_recovery_report_contains_action() -> None:
    report = evaluate_recovery(
        make_request()
    )

    assert isinstance(
        report.action,
        RecoveryAction,
    )


def test_recovery_action_component_matches_request() -> None:
    report = evaluate_recovery(
        make_request(
            component="checkpoint"
        )
    )

    assert report.action is not None

    assert (
        report.action.component
        == "checkpoint"
    )


def test_recovery_never_marks_destructive_action_safe() -> None:
    report = evaluate_recovery(
        make_request(
            failure_type="recoverable",
            destructive=True,
        )
    )

    assert report.fail_closed is True
    assert report.action is None


def test_invalid_report_cannot_be_validated() -> None:
    with pytest.raises(
        RecoveryValidationError
    ):
        validate_recovery(
            object()
        )


def test_unvalidated_report_cannot_be_accepted() -> None:
    action = RecoveryAction(
        action="RETRY_SAFE_OPERATION",
        component="execution",
        automatic=True,
    )

    report = RecoveryReport(
        schema_version="1.0",
        authority="REOS_CONTROL_CENTER",
        decision=RecoveryDecision.RECOVER,
        reason=(
            RecoveryReason.RECOVERABLE_EXECUTION_ERROR
        ),
        request_fingerprint="a" * 64,
        action=action,
        fail_closed=False,
        validated=False,
        explanation="not validated",
    )

    with pytest.raises(
        RecoveryValidationError
    ):
        validate_recovery(
            report
        )


def test_authority_is_fixed() -> None:
    report = evaluate_recovery(
        make_request()
    )

    assert report.authority == (
        "REOS_CONTROL_CENTER"
    )


def test_schema_version_is_fixed() -> None:
    report = evaluate_recovery(
        make_request()
    )

    assert report.schema_version == "1.0"


def test_algorithm_is_sha256() -> None:
    assert RecoveryGuard.ALGORITHM == "sha256"


def test_safe_failure_set_is_defined() -> None:
    assert (
        "transient"
        in RecoveryGuard.SAFE_AUTOMATIC_FAILURES
    )


def test_unsafe_failure_set_is_defined() -> None:
    assert (
        "architecture"
        in RecoveryGuard.UNSAFE_FAILURES
    )