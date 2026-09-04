"""Tests for T11 recovery provenance."""

from __future__ import annotations

import pytest

from .recovery_provenance import (
    RecoveryProvenanceEngine,
    RecoveryProvenanceError,
)


def test_t10_provenance_is_valid() -> None:
    provenance = RecoveryProvenanceEngine.build(
        source_layer="T10_DRIFT_DETECTION",
        source_identity="drift-identity",
        source_fingerprint="a" * 64,
        recovery_policy_version="T11-POLICY-1.0",
    )

    assert RecoveryProvenanceEngine.validate(
        provenance
    ) is True


def test_t09_provenance_is_valid() -> None:
    provenance = RecoveryProvenanceEngine.build(
        source_layer="T09_STATE_FINGERPRINT",
        source_identity="state-identity",
        source_fingerprint="b" * 64,
        recovery_policy_version="T11-POLICY-1.0",
    )

    assert RecoveryProvenanceEngine.validate(
        provenance
    ) is True


def test_unknown_source_is_rejected() -> None:
    with pytest.raises(RecoveryProvenanceError):
        RecoveryProvenanceEngine.build(
            source_layer="CHAT_CONTEXT",
            source_identity="chat",
            source_fingerprint="a" * 64,
            recovery_policy_version="T11-POLICY-1.0",
        )


def test_invalid_fingerprint_is_rejected() -> None:
    with pytest.raises(RecoveryProvenanceError):
        RecoveryProvenanceEngine.build(
            source_layer="T10_DRIFT_DETECTION",
            source_identity="drift",
            source_fingerprint="bad",
            recovery_policy_version="T11-POLICY-1.0",
        )


def test_authority_is_fixed() -> None:
    provenance = RecoveryProvenanceEngine.build(
        source_layer="T10_DRIFT_DETECTION",
        source_identity="drift",
        source_fingerprint="a" * 64,
        recovery_policy_version="T11-POLICY-1.0",
    )

    assert provenance.authority == (
        "REOS_CONTROL_CENTER"
    )