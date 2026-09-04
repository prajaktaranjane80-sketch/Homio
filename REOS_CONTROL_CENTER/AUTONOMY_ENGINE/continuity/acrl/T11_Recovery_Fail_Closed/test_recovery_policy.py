"""Tests for T11 recovery policy."""

from __future__ import annotations

import pytest

from .recovery_policy import (
    RecoveryPolicy,
    RecoveryPolicyEngine,
    RecoveryPolicyValidationError,
)


def test_default_policy_is_valid() -> None:
    policy = RecoveryPolicyEngine.default()

    assert RecoveryPolicyEngine.validate(policy) is True


def test_policy_version_is_fixed() -> None:
    policy = RecoveryPolicyEngine.default()

    assert policy.version == "T11-POLICY-1.0"


def test_destructive_recovery_is_forbidden() -> None:
    policy = RecoveryPolicy(
        version="T11-POLICY-1.0",
        automatic_recovery_enabled=True,
        destructive_recovery_allowed=True,
        authority_required=True,
        integrity_required=True,
        unknown_failure_fails_closed=True,
        architecture_drift_fails_closed=True,
        authority_conflict_fails_closed=True,
        integrity_failure_fails_closed=True,
    )

    with pytest.raises(RecoveryPolicyValidationError):
        RecoveryPolicyEngine.validate(policy)


def test_authority_is_mandatory() -> None:
    policy = RecoveryPolicyEngine.default()

    assert policy.authority_required is True


def test_integrity_is_mandatory() -> None:
    policy = RecoveryPolicyEngine.default()

    assert policy.integrity_required is True


def test_unknown_failure_fails_closed() -> None:
    policy = RecoveryPolicyEngine.default()

    assert policy.unknown_failure_fails_closed is True