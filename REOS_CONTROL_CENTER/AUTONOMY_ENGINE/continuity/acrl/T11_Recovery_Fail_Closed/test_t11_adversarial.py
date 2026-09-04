"""Adversarial tests for T11."""

from __future__ import annotations

import pytest

from .recovery_guard import (
    RecoveryDecision,
    RecoveryRequest,
    evaluate_recovery,
)
from .recovery_identity import (
    RecoveryIdentity,
    RecoveryIdentityEngine,
    RecoveryIdentityError,
)


def test_unknown_failure_cannot_recover() -> None:
    request = RecoveryRequest(
        failure_type="unknown",
        component="execution",
        recoverable=True,
        authoritative=True,
        integrity_verified=True,
    )

    report = evaluate_recovery(request)

    assert report.decision == (
        RecoveryDecision.FAIL_CLOSED
    )


def test_destructive_flag_overrides_recoverable() -> None:
    request = RecoveryRequest(
        failure_type="recoverable",
        component="execution",
        recoverable=True,
        authoritative=True,
        destructive=True,
        integrity_verified=True,
    )

    report = evaluate_recovery(request)

    assert report.fail_closed is True
    assert report.action is None


def test_authority_spoof_cannot_recover() -> None:
    request = RecoveryRequest(
        failure_type="timeout",
        component="execution",
        recoverable=True,
        authoritative=False,
        integrity_verified=True,
    )

    with pytest.raises(Exception):
        evaluate_recovery(request)


def test_integrity_spoof_cannot_recover() -> None:
    request = RecoveryRequest(
        failure_type="timeout",
        component="execution",
        recoverable=True,
        authoritative=True,
        integrity_verified=False,
    )

    with pytest.raises(Exception):
        evaluate_recovery(request)


def test_tampered_identity_is_rejected() -> None:
    identity = RecoveryIdentityEngine.build(
        schema_version="1.0",
        authority="REOS_CONTROL_CENTER",
        request_fingerprint="a" * 64,
        decision="RECOVER",
    )

    tampered = RecoveryIdentity(
        identity_version=identity.identity_version,
        schema_version=identity.schema_version,
        authority=identity.authority,
        request_fingerprint=identity.request_fingerprint,
        decision="FAIL_CLOSED",
        identity_fingerprint=identity.identity_fingerprint,
    )

    with pytest.raises(RecoveryIdentityError):
        RecoveryIdentityEngine.validate(tampered)