"""ACRL T11 — PART 11 Fail-Closed Recovery acceptance tests."""

from __future__ import annotations

import pytest

from AUTONOMY_ENGINE.continuity.acrl.recovery_guard import (
    RecoveryAuthorityError,
    RecoveryBlockedError,
    RecoveryDecision,
    RecoveryGuard,
    RecoveryIntegrityError,
    RecoveryReason,
    RecoveryRequest,
    RecoveryValidationError,
    evaluate_recovery,
)


def make_request(
    *,
    failure_type: str,
    recoverable: bool = True,
    authoritative: bool = True,
    integrity_verified: bool = True,
    destructive: bool = False,
) -> RecoveryRequest:
    return RecoveryRequest(
        failure_type=failure_type,
        component="continuity",
        recoverable=recoverable,
        authoritative=authoritative,
        integrity_verified=integrity_verified,
        destructive=destructive,
    )


@pytest.mark.parametrize(
    "failure_type",
    [
        "state_unavailable",
        "state_missing",
        "integrity_mismatch",
        "reconstruction_incomplete",
        "reconstruction_mismatch",
        "dependency_conflict",
        "dependency_mismatch",
        "invalid_continuity",
        "continuity_invalid",
        "continuity_mismatch",
        "stale_context",
        "drift",
        "reconstruction_invalid",
    ],
)
def test_uncertainty_never_recovers(
    failure_type: str,
) -> None:
    report = evaluate_recovery(
        make_request(
            failure_type=failure_type,
            recoverable=True,
        )
    )

    assert (
        report.decision
        == RecoveryDecision.FAIL_CLOSED
    )

    assert report.fail_closed is True
    assert report.action is None


@pytest.mark.parametrize(
    "failure_type",
    [
        "state_unavailable",
        "integrity_mismatch",
        "reconstruction_incomplete",
        "dependency_conflict",
        "invalid_continuity",
    ],
)
def test_required_failure_classes_fail_closed(
    failure_type: str,
) -> None:
    report = evaluate_recovery(
        make_request(
            failure_type=failure_type,
            recoverable=True,
        )
    )

    assert report.decision == (
        RecoveryDecision.FAIL_CLOSED
    )


def test_state_unavailable_is_not_guessed() -> None:
    report = evaluate_recovery(
        make_request(
            failure_type="state_unavailable",
            recoverable=True,
        )
    )

    assert report.fail_closed is True
    assert report.action is None
    assert report.reason == (
        RecoveryReason.UNKNOWN_FAILURE
    )


def test_integrity_mismatch_is_not_guessed() -> None:
    report = evaluate_recovery(
        make_request(
            failure_type="integrity_mismatch",
            recoverable=True,
        )
    )

    assert report.fail_closed is True
    assert report.decision == (
        RecoveryDecision.FAIL_CLOSED
    )


def test_reconstruction_incomplete_is_not_guessed() -> None:
    report = evaluate_recovery(
        make_request(
            failure_type="reconstruction_incomplete",
            recoverable=True,
        )
    )

    assert report.fail_closed is True
    assert report.action is None


def test_dependency_conflict_is_not_guessed() -> None:
    report = evaluate_recovery(
        make_request(
            failure_type="dependency_conflict",
            recoverable=True,
        )
    )

    assert report.fail_closed is True
    assert report.action is None


def test_invalid_continuity_is_not_guessed() -> None:
    report = evaluate_recovery(
        make_request(
            failure_type="invalid_continuity",
            recoverable=True,
        )
    )

    assert report.fail_closed is True
    assert report.action is None


def test_unclear_authority_stops_recovery() -> None:
    with pytest.raises(
        RecoveryAuthorityError
    ):
        evaluate_recovery(
            make_request(
                failure_type="execution_error",
                recoverable=True,
                authoritative=False,
            )
        )


def test_unverified_integrity_stops_recovery() -> None:
    with pytest.raises(
        RecoveryIntegrityError
    ):
        evaluate_recovery(
            make_request(
                failure_type="execution_error",
                recoverable=True,
                integrity_verified=False,
            )
        )


def test_invalid_input_stops_recovery() -> None:
    with pytest.raises(
        RecoveryValidationError
    ):
        evaluate_recovery(
            make_request(
                failure_type="",
                recoverable=True,
            )
        )


def test_architecture_drift_remains_fail_closed() -> None:
    report = evaluate_recovery(
        make_request(
            failure_type="architecture_drift",
            recoverable=True,
        )
    )

    assert report.decision == (
        RecoveryDecision.FAIL_CLOSED
    )


def test_unknown_failure_remains_fail_closed() -> None:
    report = evaluate_recovery(
        make_request(
            failure_type="unknown",
            recoverable=True,
        )
    )

    assert report.decision == (
        RecoveryDecision.FAIL_CLOSED
    )


def test_destructive_recovery_remains_fail_closed() -> None:
    report = evaluate_recovery(
        make_request(
            failure_type="recoverable",
            recoverable=True,
            destructive=True,
        )
    )

    assert report.decision == (
        RecoveryDecision.FAIL_CLOSED
    )

    assert report.action is None


def test_safe_transient_failure_still_recovers() -> None:
    report = evaluate_recovery(
        make_request(
            failure_type="timeout",
            recoverable=True,
        )
    )

    assert report.decision == (
        RecoveryDecision.RECOVER
    )

    assert report.fail_closed is False
    assert report.action is not None


def test_recoverable_execution_error_still_recovers() -> None:
    report = evaluate_recovery(
        make_request(
            failure_type="database_error",
            recoverable=True,
        )
    )

    assert report.decision == (
        RecoveryDecision.RECOVER
    )


def test_fail_closed_cannot_be_automatically_executed() -> None:
    request = make_request(
        failure_type="dependency_conflict",
        recoverable=True,
    )

    with pytest.raises(
        RecoveryBlockedError
    ):
        RecoveryGuard.evaluate_or_raise(
            request
        )


def test_safe_recovery_can_be_validated() -> None:
    report = evaluate_recovery(
        make_request(
            failure_type="timeout",
            recoverable=True,
        )
    )

    assert (
        RecoveryGuard.validate_action(report)
        is True
    )
