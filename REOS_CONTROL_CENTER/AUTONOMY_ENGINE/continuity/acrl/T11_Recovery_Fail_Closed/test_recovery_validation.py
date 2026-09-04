"""Tests for T11 recovery validation."""

from __future__ import annotations

import pytest

from .recovery_guard import (
    RecoveryAction,
    RecoveryDecision,
    RecoveryReason,
    RecoveryReport,
    RecoveryRequest,
)
from .recovery_validation import (
    RecoveryValidationEngine,
    RecoveryValidationError,
)


def make_request() -> RecoveryRequest:
    return RecoveryRequest(
        failure_type="transient",
        component="execution",
        recoverable=True,
        authoritative=True,
        destructive=False,
        integrity_verified=True,
    )


def test_valid_request() -> None:
    assert RecoveryValidationEngine.validate_request(
        make_request()
    ) is True


def test_invalid_authority_is_rejected() -> None:
    request = RecoveryRequest(
        failure_type="transient",
        component="execution",
        recoverable=True,
        authoritative=False,
        integrity_verified=True,
    )

    with pytest.raises(RecoveryValidationError):
        RecoveryValidationEngine.validate_request(
            request
        )


def test_invalid_integrity_is_rejected() -> None:
    request = RecoveryRequest(
        failure_type="transient",
        component="execution",
        recoverable=True,
        authoritative=True,
        integrity_verified=False,
    )

    with pytest.raises(RecoveryValidationError):
        RecoveryValidationEngine.validate_request(
            request
        )


def test_destructive_request_is_rejected() -> None:
    request = RecoveryRequest(
        failure_type="transient",
        component="execution",
        recoverable=True,
        authoritative=True,
        destructive=True,
        integrity_verified=True,
    )

    with pytest.raises(RecoveryValidationError):
        RecoveryValidationEngine.validate_request(
            request
        )


def test_fail_closed_report_is_valid() -> None:
    report = RecoveryReport(
        schema_version="1.0",
        authority="REOS_CONTROL_CENTER",
        decision=RecoveryDecision.FAIL_CLOSED,
        reason=RecoveryReason.UNKNOWN_FAILURE,
        request_fingerprint="a" * 64,
        action=None,
        fail_closed=True,
        validated=True,
        explanation="blocked",
    )

    assert RecoveryValidationEngine.validate_report(
        report
    ) is True