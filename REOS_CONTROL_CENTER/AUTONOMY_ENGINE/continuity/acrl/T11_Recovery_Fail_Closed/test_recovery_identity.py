"""Tests for T11 recovery identity."""

from __future__ import annotations

import pytest

from .recovery_identity import (
    RecoveryIdentity,
    RecoveryIdentityEngine,
    RecoveryIdentityError,
)


def test_identity_is_deterministic() -> None:
    kwargs = {
        "schema_version": "1.0",
        "authority": "REOS_CONTROL_CENTER",
        "request_fingerprint": "a" * 64,
        "decision": "RECOVER",
    }

    first = RecoveryIdentityEngine.build(**kwargs)
    second = RecoveryIdentityEngine.build(**kwargs)

    assert first.identity_fingerprint == (
        second.identity_fingerprint
    )


def test_identity_is_valid() -> None:
    identity = RecoveryIdentityEngine.build(
        schema_version="1.0",
        authority="REOS_CONTROL_CENTER",
        request_fingerprint="a" * 64,
        decision="RECOVER",
    )

    assert RecoveryIdentityEngine.validate(
        identity
    ) is True


def test_identity_fingerprint_length() -> None:
    identity = RecoveryIdentityEngine.build(
        schema_version="1.0",
        authority="REOS_CONTROL_CENTER",
        request_fingerprint="a" * 64,
        decision="BLOCK",
    )

    assert len(identity.identity_fingerprint) == 64


def test_invalid_authority_is_rejected() -> None:
    with pytest.raises(RecoveryIdentityError):
        RecoveryIdentityEngine.build(
            schema_version="1.0",
            authority="CHAT_CONTEXT",
            request_fingerprint="a" * 64,
            decision="RECOVER",
        )


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